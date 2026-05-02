# Formato CSV para importar temporadas históricas

Esta guía explica cómo preparar el archivo CSV para importar una temporada histórica desde
la pantalla **Importar temporada histórica** del panel de administración.

---

## Separador de columnas

El separador canónico es el **punto y coma** (`;`).

Si el archivo no contiene ningún `;` en la primera línea, el sistema acepta la **coma** (`,`)
como separador alternativo.

No se aceptan otros separadores (tabulador, pipe, etc.).

> **Consejo**: Google Sheets exporta con coma por defecto en configuraciones en inglés y con
> punto y coma en configuraciones en español. Verificá el separador antes de subir.

---

## Codificación

El archivo debe estar en **UTF-8**. Se tolera el BOM de UTF-8 (`\xEF\xBB\xBF`): si está
presente, se descarta silenciosamente.

Si el archivo no puede decodificarse como UTF-8 se rechaza con el error
`csv_encoding_invalid`.

---

## Estructura del archivo

```
Jugador1;Jugador2;Jugador3
15;14;13
15;0;13
0;15;14
```

### Fila de encabezado (primera fila)

- La primera fila no vacía se interpreta como la **fila de encabezado**.
- Cada columna es el nombre de un jugador **inscripto en el catálogo** (búsqueda
  sin distinguir mayúsculas, con espacios recortados).
- Si un nombre no existe en el catálogo, la importación se rechaza con
  `jugadores_no_resueltos` listando *todos* los nombres no encontrados.
- No se crean jugadores nuevos automáticamente — creálos primero desde el dashboard.
- No puede haber dos columnas con el mismo nombre (insensible a mayúsculas) en la
  misma cabecera.

### Filas de datos (reuniones)

- Cada fila representa una reunión, en orden cronológico de arriba hacia abajo.
- El sistema asigna `numero_jornada` secuencialmente (1, 2, 3…) según el orden de las filas.
- Las reuniones importadas **no tienen fecha** — se registran con `fecha = null` y se
  muestran como "Sin fecha" en la aplicación.
- Las filas completamente en blanco se ignoran.

### Puntajes

| Valor | Interpretación |
|-------|----------------|
| `0` | Jugador **ausente** — no se crea posición para este jugador en la reunión |
| `1`–`15` | Puntaje de la reunión — valor entero en el rango `[1, 15]` |

Cualquier valor que no sea un entero en `[0, 15]` (incluyendo decimales, texto, celdas
vacías) se rechaza con `puntaje_invalido`.

Una fila donde **todos** los jugadores tienen puntaje `0` se rechaza con
`reunion_todos_ausentes` — una reunión sin asistentes no es válida.

---

## Inferencia de posiciones e invitados

El sistema reconstituye las posiciones a partir de los puntajes usando la regla del juego:

- **Posición 1 = 15 pts, posición 2 = 14 pts, … posición N = 16 − N**.
- Los jugadores presentes (puntaje > 0) se ordenan de mayor a menor.
- Si hay un **hueco** en la secuencia de puntajes (por ejemplo, nadie tiene 14 pts pero
  alguien tiene 15 y el siguiente tiene 13), se infiere un **invitado** por cada puntaje
  faltante.

### Ejemplo con invitado

CSV:
```
Ana;Beto
15;13
```

Resultado reconstruido para esa reunión:

| Pos | Jugador | Puntos | Invitado |
|-----|---------|--------|----------|
| 1 | Ana | 15 | No |
| 2 | *(invitado)* | 14 | Sí |
| 3 | Beto | 13 | No |

El invitado en posición 2 se infiere porque nadie tiene el puntaje esperado de 14.
El contador `invitados_inferidos` del resumen de importación refleja cuántas posiciones de
invitado se crearon.

---

## CSV de muestra (3 jugadores, 3 reuniones, 1 invitado)

```
Ana;Beto;Carla
15;14;13
15;13;0
14;15;0
```

- **Reunión 1**: Ana (1°, 15 pts), Beto (2°, 14 pts), Carla (3°, 13 pts). Sin invitados.
- **Reunión 2**: Ana (1°, 15 pts), *(invitado)* (2°, 14 pts), Beto (3°, 13 pts), Carla ausente.
  → 1 invitado inferido.
- **Reunión 3**: Beto (1°, 15 pts), Ana (2°, 14 pts), Carla ausente. Sin invitados.

---

## Exportar desde Google Sheets

1. Abrí la planilla en Google Sheets.
2. Asegurate de que la primera fila tenga los nombres de los jugadores y las filas
   siguientes los puntajes de cada reunión.
3. Menú: **Archivo → Descargar → Valores separados por comas (.csv)**.
4. El archivo descargado usa coma (`,`) como separador en configuraciones en inglés o
   punto y coma (`;`) en español. Ambos son aceptados por el importador.
5. Si tu sistema está en inglés y quieres el separador `;`, podés cambiar la configuración
   regional de la hoja: **Archivo → Configuración de la hoja de cálculo → Configuración
   regional → seleccionar un país de habla hispana**.

---

## Errores comunes y cómo resolverlos

| Código de error | Causa | Solución |
|----------------|-------|----------|
| `csv_encoding_invalid` | El archivo no está en UTF-8 | Guardá como UTF-8 desde Excel o Google Sheets |
| `csv_invalido` | No hay estructura CSV reconocible | Verificá que el archivo tenga encabezado y filas de datos |
| `csv_sin_reuniones` | Hay encabezado pero ninguna fila de datos | Agregá las filas de puntajes |
| `jugadores_no_resueltos` | Un nombre del encabezado no existe en el catálogo | Creá el jugador desde el dashboard antes de importar |
| `puntaje_invalido` | Una celda tiene un valor fuera del rango `[0, 15]` | Corregí las celdas indicadas en el error |
| `puntajes_duplicados` | Dos jugadores tienen el mismo puntaje en la misma reunión | En Dudo cada posición es única; revisá la fila indicada |
| `reunion_todos_ausentes` | Una fila entera tiene solo ceros | Eliminá la fila o corregí los puntajes |
| `temporada_duplicada` | Ya existe una temporada con ese nombre | Usá un nombre diferente o eliminá la existente antes de reimportar |
| `campeon_no_inscripto` | El nombre del campeón no coincide con ningún encabezado del CSV | Verificá la ortografía (la búsqueda es insensible a mayúsculas) |
