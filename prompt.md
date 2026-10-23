# Voice Command API: Backend para interfaz de tareas por voz

Actúa como un **desarrollador senior** para completar la siguiente tarea.

## Contexto

Una startup de productividad ha construido una interfaz de voz que permite a sus usuarios gestionar una lista de tareas únicamente hablando. El frontend ya está listo: funciona en el navegador, captura la voz del usuario a través del micrófono y la transcribe a texto usando la **Web Speech API**. Tu trabajo es construir el backend que hace que esa interfaz funcione de verdad.

El frontend envía cada transcripción a un único endpoint de entrada: `POST /instruction`. Desde ahí, tu API debe identificar qué pidió el usuario, redirigir la petición al endpoint interno correcto y devolver una respuesta que la interfaz pueda mostrar.

El tech lead del equipo te dejó esta nota antes de irse de vacaciones:

---

## Especificaciones del backend: Voice Command API

### Punto de entrada

`POST /instruction` recibe una transcripción en texto plano y llama a la API de Groq para extraer la intención y los parámetros. Debe devolver un JSON que identifique qué endpoint llamar y con qué argumentos. El frontend usará esta respuesta para hacer la petición de seguimiento.

### Endpoints de tareas (almacenamiento en memoria, sin base de datos)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/tasks` | Devuelve la lista completa de tareas |
| `POST` | `/tasks` | Crea una nueva tarea (requiere `title`; campo opcional `done`, por defecto `false`) |
| `PUT` | `/tasks/<int:task_id>` | Reemplaza una tarea completa |
| `PATCH` | `/tasks/<int:task_id>` | Marca una tarea como completada o actualiza el título |
| `DELETE` | `/tasks/<int:task_id>` | Elimina una tarea por ID |

### Almacenamiento

Usa una **lista a nivel de módulo** como almacén de datos. Cada tarea es un diccionario con `id`, `title` y `done`. Sin base de datos, sin sistema de archivos.

### Integración con Groq

Usa la API de Groq desde tu endpoint `/instruction`. El enunciado original sugería el modelo `llama3-8b-8192` "o similar". El *system prompt* debe instruir al LLM para que responda **únicamente** con un objeto JSON en este formato exacto:

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": { "title": "Comprar leche" }
}
```

El LLM **nunca** debe devolver texto libre, solo ese JSON. Tu ingeniería de prompt es lo que hace que esto funcione.

> **Nota sobre el modelo:** `llama3-8b-8192` fue deprecado por Groq (agosto de 2025) y su reemplazo `llama-3.1-8b-instant` también está deprecado (agosto de 2026). Antes de escribir código, **verifica los modelos vigentes** en https://console.groq.com/docs/models y en https://console.groq.com/docs/deprecations, o consultando `GET https://api.groq.com/openai/v1/models` con tu API key. Una opción recomendada por Groq como reemplazo es `openai/gpt-oss-20b`, pero comprueba que responda bien en modo JSON. Guarda el nombre del modelo en una variable de entorno (por ejemplo `GROQ_MODEL` en `.env`) para poder cambiarlo sin tocar el código.

La PM de la startup quiere ver el flujo completo de voz a acción funcionando de extremo a extremo: el usuario dice *"añade comprar leche a mi lista"* y la tarea aparece. Ese es tu objetivo.

---

## Qué debes hacer

### 1. Configuración

- Crea un entorno virtual e instala **FastAPI**, **Uvicorn** y el **SDK de Python de Groq**.
- Guarda la API Key de Groq (y el nombre del modelo) en un archivo `.env` para que no se suba al repositorio.
- **Agrega `.env` al archivo `.gitignore` antes del primer commit.** Crear el `.env` no basta: si no está en `.gitignore`, Git lo subirá. Incluye también la carpeta del entorno virtual (`venv/` o `.venv/`) y `__pycache__/`. Si la clave llegara a subirse por error, revócala en la consola de Groq y genera una nueva, porque borrar el archivo después no elimina el historial de Git.
- Crea un archivo `.env.example` (sin valores reales) para documentar qué variables necesita el proyecto.
- Configura **CORS** para que el frontend pueda comunicarse con la API.

### 2. Almacenamiento en memoria

- Declara una lista a nivel de módulo llamada `tasks` para usarla como almacén de datos.
- Cada tarea debe tener:
  - `id` (entero)
  - `title` (cadena de texto)
  - `done` (booleano, por defecto `false`)

### 3. Endpoints de tareas

- `GET /tasks`: devuelve todas las tareas como un array JSON.
- `POST /tasks`: crea una tarea a partir del cuerpo de la petición y la añade a la lista. Devuelve la tarea creada con su ID asignado.
- `PUT /tasks/<task_id>`: reemplaza el objeto de la tarea completo para el ID indicado.
- `PATCH /tasks/<task_id>`: actualiza parcialmente una tarea (título y/o estado `done`).
- `DELETE /tasks/<task_id>`: elimina la tarea con el ID indicado y devuelve un mensaje de confirmación.

### 4. Endpoint de instrucción

- `POST /instruction` recibe un cuerpo JSON con un campo `transcription` (texto plano).
- Llama a la API de Groq con un *system prompt* adecuado que fuerce al LLM a responder únicamente con un objeto JSON estructurado que indique `endpoint`, `method` y `params`.
- Devuelve ese JSON directamente al frontend.

### 5. Conexión extremo a extremo

Usando la respuesta de `/instruction`, el frontend llama automáticamente al endpoint de tareas correcto. Verifica que esto funcione, hablando en voz alta, al menos para:

- Crear tareas
- Listar tareas
- Actualizar tareas
- Eliminar tareas

---

## ⚠️ Restricciones importantes

1. **No uses bases de datos.** Todos los datos deben vivir en una lista de Python en memoria. La lista se reinicia cada vez que el servidor se reinicia; ese es el comportamiento esperado para este proyecto.

2. **El endpoint `/instruction` no debe contener lógica de detección de intención codificada manualmente** (por ejemplo, nada de `if "añade" in text`). Todas las decisiones de enrutamiento deben provenir de la respuesta del LLM.

3. Asegúrate de que el **repositorio sea público** y de que el `README.md` esté en la **raíz**.

4. **Nunca subas secretos al repositorio.** `.env` debe estar en `.gitignore` y la API Key no debe aparecer en el código, en el README ni en capturas de pantalla.

---

## Entregable final

Una vez concluidas tus tareas, crea un archivo `LEARNING.md` donde me expliques todo lo que hiciste. Considera que lo usaré para **aprender**, por lo que debes ser **pedagógico** en la explicación. Incluye una sección sobre cómo elegiste el modelo de Groq y por qué verificaste que siguiera vigente.

---

## Resumen de entregables

| Entregable | Ubicación | Notas |
|---|---|---|
| Backend FastAPI (`/tasks` + `/instruction`) | Repositorio | Almacenamiento en memoria, CORS configurado |
| `.env` con la API Key y el modelo de Groq | Local (no se sube) | Debe estar en `.gitignore` desde el primer commit |
| `.env.example` | Repositorio | Solo nombres de variables, sin valores reales |
| `.gitignore` | Raíz del repositorio | Incluye `.env`, `venv/` y `__pycache__/` |
| `README.md` | Raíz del repositorio | Repositorio público |
| `LEARNING.md` | Repositorio | Explicación pedagógica de todo el proceso |