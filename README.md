# Conciliacion Vega Supermercados

Sistema de conciliacion automatica entre movimientos bancarios y archivos TRS de los locales de Vega.

El proyecto procesa archivos de banco en PDF o Excel, cruza la informacion contra los TRS de caja, clasifica coincidencias y genera reportes por dia, por rango y resumenes historicos en Excel.

## Objetivo

Automatizar la conciliacion entre:

- Banco: movimientos bancarios entregados por la entidad financiera.
- Caja: archivos TRS de cada local.

El cruce principal se hace por:

- `Nro. Documento`
- `Monto`

Con ese cruce el sistema determina si una transaccion:

- `COINCIDE`
- `REVISAR`
- `NO COINCIDE`

## Caracteristicas principales

- Soporta Banco en `PDF`, `XLS`, `XLSX`, `XLSM` y `XLSB`.
- Soporta multiples formatos historicos del banco.
- Detecta automaticamente si el procesamiento es diario o por rango.
- Limpia y normaliza fechas, montos y numeros de documento antes de conciliar.
- Genera reportes separados por movimientos, por local y consolidado.
- Mantiene resumenes historicos mensuales sin duplicar filas ya agregadas.
- Funciona en entorno local Windows y en Google Colab.

## Flujo general

1. `main.py` prepara el entorno y limpia subcarpetas de salida temporales.
2. Se detectan archivos en `input/` y `input_date_range/`.
3. El sistema identifica archivos Banco y TRS por nombre y extension.
4. Los loaders limpian y estandarizan la informacion.
5. `core.conciliador` cruza Banco vs Caja.
6. `export/` genera archivos Excel por dia o por rango.
7. Se actualizan los resumenes historicos:
   - `output/resumen_mensual.xlsx`
   - `output/resumen_mensual_rango.xlsx`

## Arquitectura

### Punto de entrada

- `main.py`
  - Inicializa entorno.
  - Ejecuta limpieza previa.
  - Lanza procesamiento diario y/o por rango.
  - Captura errores globales e interrupciones manuales.

### Configuracion y rutas

- `config.py`
  - Expone rutas principales y catalogo de locales.
- `utils/environment.py`
  - Detecta si se ejecuta en local o Colab.
  - Permite override de ruta base con `CONCILIACION_DRIVE_PATH`.
- `utils/path_manager.py`
  - Define carpetas de `input`, `output`, `por_dia`, `por_rango`, etc.

### Deteccion de archivos

- `detect.py`
  - Detecta archivos Banco y TRS.
  - Extrae fecha desde el nombre del archivo.
  - Acepta Banco en `PDF`, `XLS`, `XLSX`, `XLSM`, `XLSB`.
- `services/input_detector.py`
  - Fachada para deteccion diaria y por rango.

### Nucleo de conciliacion

- `core/runner.py`
  - Orquesta lectura, conciliacion, exportacion y QA.
- `core/conciliador.py`
  - Normaliza documento y monto.
  - Evalua coincidencia Banco vs TRS.
- `core/evaluador.py`
  - Define estados y detalle de revision.
- `core/utils.py`
  - Normaliza documentos, montos y limpia caracteres ilegales.

### Loaders

- `loaders/mov_excel.py`
  - Parser flexible para movimientos bancarios en Excel.
  - Soporta:
    - Excel con metadata en filas superiores y encabezado real mas abajo.
    - Excel tabular exportado desde PDF.
    - Excel legacy historico.
- `loaders/pdf_dispatcher.py`
  - Detecta modelo PDF y lo enruta al parser correcto.
- `loaders/pdf_models/model_1.py`
  - Selecciona parser segun la firma real del PDF.
- `loaders/mov_pdf_header_unica.py`
  - PDF con header unico tipo `FECHA OFICINA TIPO CONCEPTO ...`.
- `loaders/mov_pdf2.py`
  - PDF tipo `Fecha Concepto Tipo Monto Saldo Documento Beneficiaria`.
- `loaders/mov_pdf_portada.py`
  - Variante con portada y lineas de texto en bloque.
- `loaders/trs.py`
  - Limpia archivos TRS de cada local.

### Exportacion

- `services/export_service.py`
  - Ejecuta conciliacion y exportacion.
  - Valida QA minima de archivos generados.
- `export/excel.py`
  - Genera reportes principales.
- `export/resumen_diario.py`
  - Calcula errores y totales por caja.
- `export/resumen_mensual.py`
  - Guarda historico mensual sin duplicados.
- `export/pdf.py`
  - Utilidad legacy para convertir Excel a PDF en algunos flujos.

### Limpieza

- `clean.py`
  - Borra archivos de `input/` e `input_date_range/`.
  - Resetea carpetas `output/por_dia` y `output/por_rango`.
- `utils/cleaner.py`
  - Implementacion de limpieza.

### Tests

- `tests/test_mov_excel.py`
- `tests/test_mov_pdf_header_unica.py`
- `tests/test_pdf_model_1.py`

## Estructura del proyecto

```text
Conciliacion/
|-- main.py
|-- config.py
|-- detect.py
|-- requirements.txt
|-- input/
|-- input_date_range/
|-- output/
|   |-- por_dia/
|   |-- por_rango/
|   |-- resumen_mensual.xlsx
|   `-- resumen_mensual_rango.xlsx
|-- core/
|-- loaders/
|   `-- pdf_models/
|-- services/
|-- export/
|-- utils/
`-- tests/
```

## Requisitos

- Python 3.12+ recomendado
- Windows PowerShell para uso local
- Dependencias del proyecto:
  - `pandas`
  - `openpyxl`
  - `xlrd`
  - `pyxlsb`
  - `pdfplumber`
  - `reportlab`

## Instalacion

### Opcion 1: usar entorno virtual local

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Opcion 2: ejecutar con el Python del entorno ya creado

```powershell
venv\Scripts\python.exe main.py
```

Importante:

- Si se ejecuta `python main.py` con otro Python distinto al del entorno, puede fallar por dependencias faltantes.
- La forma recomendada en Windows para este proyecto es:

```powershell
venv\Scripts\python.exe main.py
```

## Ejecucion

### Proceso principal

```powershell
venv\Scripts\python.exe main.py
```

### Limpieza manual de inputs y salidas temporales

```powershell
venv\Scripts\python.exe clean.py
```

### Ejecutar tests

```powershell
venv\Scripts\python.exe -m unittest tests.test_mov_excel tests.test_mov_pdf_header_unica tests.test_pdf_model_1
```

## Modos de trabajo

### 1. Modo diario

Usa archivos colocados en `input/`.

Procesa una fecha puntual por cada conjunto Banco + TRS.

Ejemplo:

```text
input/
|-- Mis Movimientos 05-03-2026.xlsb
|-- trs-vs-05-03-2026.xls
|-- trs-vm-05-03-2026.xls
|-- trs-sv-05-03-2026.xls
`-- trs-v2-05-03-2026.xls
```

### 2. Modo rango

Usa archivos colocados en `input_date_range/`.

Procesa lotes de varias fechas como un solo bloque.

Ejemplo:

```text
input_date_range/
|-- Mis Movimientos 07 al 09-03-2026.pdf
|-- trs-vs-07-a-09-03-2026.xls
|-- trs-vm-07-a-09-03-2026.xls
|-- trs-sv-07-a-09-03-2026.xls
`-- trs-v2-07-a-09-03-2026.xls
```

## Convenciones de nombres

### Banco

Para que el archivo Banco sea detectado correctamente, debe cumplir estas condiciones:

- Tener una fecha en el nombre con patron `dd-mm-yyyy`, `dd_mm_yyyy` o `dd.mm.yyyy`.
- No contener `trs` en el nombre.
- Tener extension soportada.

Ejemplos validos:

- `Mis Movimientos 05-03-2026.xlsb`
- `Banco 06-03-2026.pdf`
- `Estado Cuenta 07_03_2026.xlsx`

### TRS

Los TRS deben incluir el codigo del local en el nombre.

Patron esperado:

- `trs-<codigo>-<fecha>.xls`
- `trs_<codigo>_<fecha>.xls`

Codigos soportados:

| Codigo | Local |
|---|---|
| `vs` | Vega Supermercado |
| `vm` | Vega Mayorista |
| `sv` | Super Vega |
| `v2` | Vega Supermercado 2 |

Ejemplos validos:

- `trs-vs-05-03-2026.xls`
- `trs-vm-05-03-2026.xls`
- `trs-sv-05-03-2026.xls`
- `trs-v2-05-03-2026.xls`

## Como detecta los archivos el sistema

### Diario

- Extrae la fecha desde el nombre.
- Si el archivo es Banco, lo guarda como fuente de movimientos de esa fecha.
- Si el archivo es TRS, lo agrupa por local.
- Solo procesa fechas que tengan Banco y al menos un TRS.

### Rango

- Agrupa archivos del rango usando los dos primeros numeros sueltos del nombre.
- Por eso conviene mantener nombres consistentes del tipo:
  - `07 al 09-03-2026`
  - `07-a-09-03-2026`

Recomendacion:

- Mantener un formato estable de nombres para que el rango quede claro en la carpeta y en el consolidado.

## Formatos Banco soportados hoy

### Excel con metadata arriba

Caso real soportado:

- El banco entrega un `XLSB` con filas informativas arriba.
- El header real puede arrancar despues de las primeras 6 filas.
- El sistema detecta automaticamente la fila del encabezado.

Columnas esperadas o equivalentes:

- `Fecha`
- `Concepto`
- `Tipo`
- `Monto`
- `Saldo Contable` o `Saldo`
- `Documento`

Este fue el caso agregado para:

- `Mis Movimientos 05-03-2026.xlsb`

### Excel tabular exportado desde PDF

Columnas tipicas:

- `FECHA`
- `DESCRIPCION`
- `NUMERO DE DOCUMENTO`
- `DEBITO`
- `CREDITO`
- `SALDO`

### Excel legacy historico

Formato anterior que el proyecto ya soportaba y se mantiene por compatibilidad.

### PDF modelo 1

Variantes principales:

- Header unico:
  - `FECHA OFICINA TIPO CONCEPTO NRO DOCUMENTO MONTO SALDO`
- Layout tipo documento beneficiaria:
  - `Fecha Concepto Tipo Monto Saldo Documento Beneficiaria`
- Variante de portada con lineas de texto y transacciones embebidas.

### PDF modelo 2

Formato legacy de PDF con columnas tipo:

- `FECHA`
- `OFICINA`
- `CONCEPTO`
- `DEBITO`
- `CREDITO`
- `SALDO`

## Estandar interno de columnas

Sin importar si el archivo original viene en PDF o Excel, el sistema intenta transformar movimientos Banco a estas columnas:

| Columna | Descripcion |
|---|---|
| `Fecha` | Fecha normalizada |
| `Concepto` | Descripcion del movimiento |
| `Tipo` | Tipo del movimiento |
| `Monto` | Valor del movimiento |
| `Saldo` | Saldo despues del movimiento |
| `Nro. Documento` | Documento o voucher del banco |
| `Recaudador` | Caja detectada desde el texto si existe |

En TRS se usan principalmente:

| Columna | Descripcion |
|---|---|
| `Fecha` | Fecha del TRS |
| `Factura` | Factura derivada desde Documentos |
| `Recaudador` | Caja detectada |
| `Nro. Documento` | Voucher |
| `Valor` | Monto del TRS |
| `Detalle` | Detalle del pago |

## Logica de conciliacion

La conciliacion compara Banco contra Caja asi:

1. Normaliza `Nro. Documento`.
2. Normaliza `Monto`.
3. Busca coincidencia exacta por `(documento, monto)`.

### Estados

#### COINCIDE

Se encontro la misma pareja:

- mismo documento
- mismo monto

#### REVISAR

Se usa cuando hay coincidencia parcial:

- documento y monto existen, pero no como pareja exacta
- solo coincide el monto
- solo coincide el documento

#### NO COINCIDE

No existe coincidencia ni por documento ni por monto.

## Salidas generadas

### Salida diaria

Carpeta:

- `output/por_dia/<fecha>/`

Archivos esperados cuando estan los 4 locales:

- `conciliacion_movimientos_<fecha>.xlsx`
- `conciliacion_trs_vs_<fecha>.xlsx`
- `conciliacion_trs_vm_<fecha>.xlsx`
- `conciliacion_trs_sv_<fecha>.xlsx`
- `conciliacion_trs_v2_<fecha>.xlsx`
- `conciliacion_consolidado_<fecha>.xlsx`

Ejemplo:

```text
output/por_dia/05_03_2026/
|-- conciliacion_movimientos_05_03_2026.xlsx
|-- conciliacion_trs_vs_05_03_2026.xlsx
|-- conciliacion_trs_vm_05_03_2026.xlsx
|-- conciliacion_trs_sv_05_03_2026.xlsx
|-- conciliacion_trs_v2_05_03_2026.xlsx
`-- conciliacion_consolidado_05_03_2026.xlsx
```

### Salida por rango

Carpeta:

- `output/por_rango/<fecha_min>__<fecha_max>/`

Archivos esperados:

- `conciliacion_movimientos_<rango_key>.xlsx`
- `conciliacion_trs_<local>_<rango_key>.xlsx`
- `conciliacion_consolidado_<fecha_min>__<fecha_max>.xlsx`

Ejemplo:

```text
output/por_rango/07_03_2026__09_03_2026/
|-- conciliacion_movimientos_07-09.xlsx
|-- conciliacion_trs_vs_07-09.xlsx
|-- conciliacion_trs_vm_07-09.xlsx
|-- conciliacion_trs_sv_07-09.xlsx
|-- conciliacion_trs_v2_07-09.xlsx
`-- conciliacion_consolidado_07_03_2026__09_03_2026.xlsx
```

### Resumenes historicos

- `output/resumen_mensual.xlsx`
- `output/resumen_mensual_rango.xlsx`

Estos archivos:

- agregan resultados por fecha, sucursal y caja
- son idempotentes
- evitan duplicados al reejecutar

## Limpieza automatica

Al iniciar `main.py`:

- se limpian solo las subcarpetas de `output/por_dia`
- se limpian solo las subcarpetas de `output/por_rango`
- no se borran automaticamente los resumenes historicos mensuales

Al ejecutar `clean.py`:

- se borran archivos de `input/`
- se borran archivos de `input_date_range/`
- se resetean `output/por_dia` y `output/por_rango`

## QA y validaciones internas

El proyecto tiene validaciones basicas de QA:

- detecta fechas huerfanas sin Banco o sin TRS
- valida que se exporten los archivos esperados
- marca dias incompletos si faltan locales
- resume el resultado al final de la ejecucion

Salida final tipica:

```text
QA RESULTADO:
- Inputs validados
- Limpieza correcta
- Exportacion correcta
- Compatible con Colab
```

## Soporte para Colab

El proyecto puede correr en Google Colab.

Reglas:

- Si detecta Colab, usa por defecto:
  - `/content/drive/MyDrive/Conciliacion`
- Si se define la variable de entorno `CONCILIACION_DRIVE_PATH`, esa ruta tiene prioridad.

## Mantenimiento futuro

Esta seccion esta pensada para no tener que volver a inspeccionar todo el codigo cuando aparezca un formato nuevo.

### Si llega un nuevo Excel del banco

Revisar primero:

- `loaders/mov_excel.py`

Regla de implementacion:

1. Detectar la firma del nuevo formato.
2. Mapear sus columnas al estandar interno.
3. Conservar estas columnas finales:
   - `Fecha`
   - `Concepto`
   - `Tipo`
   - `Monto`
   - `Saldo`
   - `Nro. Documento`
   - `Recaudador`
4. Agregar test en `tests/test_mov_excel.py`.

### Si llega un nuevo PDF del banco

Revisar primero:

- `loaders/pdf_dispatcher.py`
- `loaders/pdf_models/model_1.py`
- `loaders/mov_pdf_header_unica.py`
- `loaders/mov_pdf2.py`
- `loaders/mov_pdf_portada.py`

Regla de implementacion:

1. Identificar la firma textual de las primeras paginas.
2. Decidir si entra en `PDF_MODEL_1`, `PDF_MODEL_2` o un modelo nuevo.
3. Crear o ajustar parser.
4. Mantener la salida canonica.
5. Agregar test en `tests/`.

### Si aparece un nuevo local

Actualizar:

- `config.py`

Campos a revisar:

- `LOCALES`
- `LOCALES_DISPLAY`

Tambien asegurarse de que los nombres de archivo TRS usen el nuevo codigo.

## Troubleshooting

### `ModuleNotFoundError: No module named 'pandas'`

Se esta ejecutando con un Python que no tiene las dependencias instaladas.

Solucion:

```powershell
venv\Scripts\python.exe main.py
```

o bien:

```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### El Banco vino en Excel y antes solo funcionaba PDF

Ya esta soportado. El sistema detecta automaticamente Banco en:

- `PDF`
- `XLS`
- `XLSX`
- `XLSM`
- `XLSB`

### El Excel del banco tiene filas informativas arriba

Ya esta soportado. El loader busca automaticamente la fila real del encabezado.

### El proceso tarda mucho en PDF

El proyecto ahora enruta el parser segun la firma del PDF. Si aparece un PDF nuevo que tarda demasiado:

1. revisar `loaders/pdf_models/model_1.py`
2. inspeccionar texto de la primera pagina
3. agregar o ajustar regla de enrutamiento

### Se interrumpio con `Ctrl+C`

`main.py` captura `KeyboardInterrupt` y marca la ejecucion como interrumpida por el usuario.

## Estado actual documentado

Este README ya contempla el soporte agregado para:

- Banco en Excel `XLSB` con metadata superior
- Banco en PDF o Excel detectado dentro del mismo pool de opciones
- Conciliacion usando `Nro. Documento` y `Monto`
- Ruteo mas preciso para PDFs del modelo principal

## Recomendacion para GitHub

Antes de publicar el repositorio, conviene no subir:

- `venv/`
- `__pycache__/`
- `output/`
- archivos reales de `input/`

Eso normalmente se resuelve con un `.gitignore`.

## Resumen corto

Si en el futuro solo necesitas recordar como funciona el proyecto, esta es la idea central:

- se colocan archivos Banco y TRS en la carpeta correcta
- el sistema detecta si son diarios o de rango
- limpia y normaliza ambos lados
- concilia por documento y monto
- genera reportes por movimientos, por local, consolidado y resumen historico
- soporta PDF y Excel del banco, incluyendo `XLSB`
