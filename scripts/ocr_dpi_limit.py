"""小さな高解像度画像による頁全体の巨大化を防ぐOCRmyPDF 17用拡張。"""

import logging
import subprocess

from ocrmypdf import hookimpl
from ocrmypdf._exec import ghostscript
from ocrmypdf.helpers import Resolution
from ocrmypdf.exceptions import SubprocessOutputError


@hookimpl
def rasterize_pdf_page(input_file, output_file, raster_device, raster_dpi,
                       pageno, page_dpi, rotation, filter_vector,
                       stop_on_soft_error, options, use_cropbox):
    factor = min(1.0, 300.0 / max(raster_dpi.x, raster_dpi.y))
    if factor == 1.0:
        return None  # 通常の頁は標準の描画処理へ渡す。
    logging.getLogger(__name__).warning('頁%dの描画解像度を300 dpiへ制限', pageno)
    raster_dpi = Resolution(raster_dpi.x * factor, raster_dpi.y * factor)
    if page_dpi is not None:
        page_dpi = Resolution(page_dpi.x * factor, page_dpi.y * factor)
    try:
        ghostscript.rasterize_pdf(input_file, output_file, raster_device=raster_device,
                                 raster_dpi=raster_dpi, pageno=pageno, page_dpi=page_dpi,
                                 rotation=rotation, filter_vector=filter_vector,
                                 stop_on_error=stop_on_soft_error, use_cropbox=use_cropbox)
    except SubprocessOutputError:
        if rotation or filter_vector or use_cropbox or raster_dpi != page_dpi:
            raise  # 未対応の変換条件を黙って変更しない。
        logging.getLogger(__name__).warning('頁%dをPopplerで再描画する', pageno)
        subprocess.run(['pdftoppm', '-f', str(pageno), '-l', str(pageno),
                        '-r', str(raster_dpi.x), '-singlefile', '-png',
                        str(input_file), str(output_file.with_suffix(''))], check=True,
                       stdout=subprocess.DEVNULL)
    return output_file
