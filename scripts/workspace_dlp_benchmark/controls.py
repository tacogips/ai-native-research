"""先頭・末尾の語句対照を、単一または分割した検知器で照合する。"""
import re

from common import object_digest

MAX_WORDS = 950
MAX_WORD_BYTES = 60 * 1024
MAX_CONTROL_WORD_CHARS = 40  # 対照語に課すこの実装の既存条件。製品一般の文字数上限ではない。


def control_references(role):
    """旧単一形式と新しい分割形式を一意に正規化する。曖昧な併用は拒否。"""
    if not isinstance(role, dict) or role.get('control_kind', 'word_list') != 'word_list':
        raise ValueError('対照には語句一覧検知器を使ってください')
    if 'control_detectors' in role:
        if 'detector_id' in role or 'detector_sha256' in role:
            raise ValueError('単一の対照指定と分割した対照指定は併用できません')
        references = role['control_detectors']
        if not isinstance(references, list) or not references:
            raise ValueError('分割した対照には空でない検知器一覧が必要です')
        if any(not isinstance(ref, dict) or set(ref) != {'id', 'sha256'} for ref in references):
            raise ValueError('各対照検知器にはidとsha256が必要です')
    else:
        references = [{'id': role.get('detector_id'), 'sha256': role.get('detector_sha256')}]
    ids = set()
    result = []
    for reference in references:
        ident, fingerprint = reference['id'], reference['sha256']
        if (not isinstance(ident, str) or not re.fullmatch(r'policies/[A-Za-z0-9_-]+', ident)
                or not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint)):
            raise ValueError('対照検知器の資源名・全文SHA-256が不正です')
        if ident in ids:
            raise ValueError('同じ対照検知器が重複しています')
        ids.add(ident)
        result.append({'id': ident, 'sha256': fingerprint})
    return result


def control_expression(role):
    references = control_references(role)
    expressions = [f"body.matches_word_list('{ref['id']}', {{minimum_match_count: 1, minimum_unique_match_count: 1}})"
                   for ref in references]
    # 旧単一形式の保存済み条件式との完全一致を維持する。
    return expressions[0] if len(expressions) == 1 else ' || '.join('(' + expr + ')' for expr in expressions)


def control_expressions(roles):
    references = {edge: control_references(roles[edge]) for edge in ('head', 'tail')}
    if ({ref['id'] for ref in references['head']} & {ref['id'] for ref in references['tail']}):
        raise ValueError('先頭と末尾の対照検知器IDは重複できません')
    return {edge: control_expression(roles[edge]) for edge in ('head', 'tail')}


def validate_wordlist_controls(roles, policies, positive_policy):
    """各検知器の証拠と語句を照合し、edge別に元の語句の集合を返す。"""
    references = {edge: control_references(roles[edge]) for edge in ('head', 'tail')}
    if ({ref['id'] for ref in references['head']} & {ref['id'] for ref in references['tail']}):
        raise ValueError('先頭と末尾の対照検知器IDは重複できません')
    unions = {}
    for edge in ('head', 'tail'):
        words_union, normalized_union = set(), set()
        for reference in references[edge]:
            detector = policies.get(reference['id'])
            if (not detector or object_digest(detector) != reference['sha256']
                    or detector.get('setting', {}).get('type') != 'settings/detector.word_list'
                    or detector.get('policyQuery') != positive_policy.get('policyQuery')
                    or detector.get('customer') != positive_policy.get('customer')):
                raise ValueError('対照検知器の全文・顧客・適用範囲が一致しません')
            word_list = detector['setting'].get('value', {}).get('wordList')
            if not isinstance(word_list, dict) or set(word_list) != {'words'}:
                raise ValueError('対照の語句一覧の定義が不明です')
            words = word_list['words']
            if (not isinstance(words, list) or not 1 <= len(words) <= MAX_WORDS
                    or any(not isinstance(word, str) or not 2 <= len(word) <= MAX_CONTROL_WORD_CHARS for word in words)):
                raise ValueError('対照の語数・語句形式が実装の条件外です')
            if len(','.join(words).encode('utf-8')) > MAX_WORD_BYTES:
                raise ValueError('対照の語句一覧が60KBを超えています')
            for word in words:
                # 語句一覧は大文字小文字・記号を無視するため、その違いだけの重複も拒否する。
                normalized = ''.join(char for char in word.casefold() if char.isalnum())
                if len(normalized) < 2 or normalized in normalized_union:
                    raise ValueError('対照語が空・短すぎる、または分割をまたいで重複しています')
                normalized_union.add(normalized)
                words_union.add(word)
        unions[edge] = words_union
    return unions
