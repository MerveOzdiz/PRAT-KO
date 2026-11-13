import csv
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring
from openpyxl import DEFUSEDXML, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from services.owner_catalog_service import FIELDS


MAX_FILE_BYTES = 1024 * 1024
MAX_ROWS = 500
SUPPORTED_EXTENSIONS = ('.csv', '.xlsx')


def csv_records(content):
    decoded = content.decode('utf-8-sig')
    if '\x00' in decoded:
        raise ValueError('CSV dosyası metin içermeli.')
    first_line = decoded.partition('\n')[0]
    delimiter = ';' if ';' in first_line else ','
    reader = csv.reader(StringIO(decoded, newline=''), delimiter=delimiter, strict=True)
    try:
        while True:
            row_number = reader.line_num + 1
            row = next(reader, None)
            if row is None:
                break
            yield row_number, row, None
    except csv.Error as exc:
        raise ValueError(f'CSV biçimi bozuk. Satır {reader.line_num}.') from exc


def xlsx_records(content):
    with ZipFile(BytesIO(content)) as archive:
        entries = archive.infolist()
        names = {entry.filename for entry in entries}
        if (len(entries) > 200 or len(names) != len(entries)
                or sum(entry.file_size for entry in entries) > 12 * 1024 * 1024):
            raise ValueError('Excel dosyasının açılmış boyutu veya parça sayısı sınırı aşıyor.')
        if not {'[Content_Types].xml', 'xl/workbook.xml'} <= names:
            raise ValueError('Geçerli bir XLSX dosyası gerekli.')
        manifest = fromstring(archive.read('[Content_Types].xml'), forbid_dtd=True)
        workbook_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'
        if not any(node.get('PartName') == '/xl/workbook.xml' and node.get('ContentType') == workbook_type
                   for node in manifest):
            raise ValueError('Makro içermeyen XLSX dosyası gerekli.')
        for name in names:
            lower = name.lower()
            if (name.startswith('/') or '\\' in name or '..' in name.split('/')
                    or lower.startswith(('xl/externallinks/', 'xl/embeddings/', 'xl/activex/'))
                    or 'vbaproject' in lower):
                raise ValueError('Excel dosyası desteklenmeyen veya etkin içerik içeriyor.')
    if not DEFUSEDXML:
        raise RuntimeError('Safe XLSX parsing requires defusedxml')
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=False, keep_links=False)
    try:
        if len(workbook.sheetnames) != 1 or len(workbook.worksheets) != 1:
            raise ValueError('Excel dosyası tek bir çalışma sayfası içermeli.')
        sheet = workbook.worksheets[0]
        sheet.reset_dimensions()
        for number, cells in enumerate(sheet.iter_rows(), start=1):
            values = [cell.value for cell in cells]
            while values and values[-1] is None:
                values.pop()
            error = ('Formül veya Excel hata hücresi desteklenmiyor.'
                     if any(cell.data_type in ('f', 'e') for cell in cells) else None)
            yield number, values, error
    finally:
        workbook.close()


def parse_upload(filename, content):
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError('Yalnızca CSV ve XLSX dosyaları desteklenir.')
    records = csv_records(content) if extension == '.csv' else xlsx_records(content)
    try:
        _, header, header_error = next(records, (1, [], None))
        columns = [value.strip().lower() if isinstance(value, str) else '' for value in header]
        if header_error or len(columns) != len(FIELDS) or set(columns) != set(FIELDS):
            raise ValueError('Dosya başlıkları şu sütunları içermeli: ' + ', '.join(FIELDS))
        result = []
        for index, values, error in records:
            if index > MAX_ROWS + 1:
                raise ValueError(f'Dosya en çok {MAX_ROWS} veri satırı içerebilir.')
            if not error and not any(value is not None and str(value).strip() for value in values):
                continue
            if not error and len(values) != len(columns):
                error = 'Satırdaki sütun sayısı başlıkla eşleşmiyor.'
            result.append((index, dict(zip(columns, values)), error))
        if not result:
            raise ValueError('Dosyada veri satırı bulunamadı.')
        return result
    except UnicodeError as exc:
        raise ValueError('CSV dosyasını UTF-8 kodlamasıyla kaydedin.') from exc
    except (BadZipFile, InvalidFileException, ParseError, DefusedXmlException,
            OSError, KeyError, IndexError, TypeError, RuntimeError, OverflowError) as exc:
        raise ValueError('Dosya bozuk veya güvenli biçimde okunamadı.') from exc
    finally:
        records.close()
