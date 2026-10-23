# Guía de aprendizaje: Voice Command API

## Qué hace el proyecto

El navegador graba la voz y envía el audio a `POST /transcribe`. El backend usa Groq para convertirlo en texto, envía esa transcripción a `POST /instruction` para obtener una acción y ejecuta esa acción sobre la lista de tareas en memoria. La respuesta incluye la transcripción, la instrucción elegida y el resultado; así, la interfaz puede mostrar qué entendió el sistema y qué cambió.

También se puede enviar una transcripción directamente a `/transcribe` como JSON. El endpoint público `/instruction` solo interpreta la transcripción y devuelve la ruta, el método y los parámetros; no modifica tareas por sí mismo.

## Cómo se organiza el backend

- `src/app/main.py` crea FastAPI, habilita CORS para los orígenes configurados e incorpora los routers.
- `src/app/schemas/voice.py` define los contratos con Pydantic. FastAPI valida las entradas y estructura las respuestas con esos modelos.
- `src/app/api/routes/tasks.py` declara la lista global `tasks` y ofrece el CRUD. Los datos desaparecen al reiniciar el proceso, tal como pide el ejercicio.
- `src/app/api/routes/instruction.py` expone la interpretación de texto sin ejecutar la tarea.
- `src/app/api/routes/transcribe.py` acepta audio o una transcripción JSON, reutiliza la misma interpretación y ejecuta la operación resultante.
- `src/app/services/voice.py` contiene las llamadas a Groq, las validaciones de la instrucción y el despacho a las funciones CRUD.

No se utiliza una base de datos ni archivos para almacenar tareas. Las rutas de elementos tienen un ID entero; una referencia que no existe responde con `404`.

## Cómo se controlan las instrucciones

El *system prompt* pide un único objeto JSON con `endpoint`, `method` y `params`. La llamada de chat también configura `response_format` como `json_object`, de modo que la API solicite JSON en lugar de prosa. Después, Pydantic valida la estructura y el backend limita las rutas y combinaciones de métodos aceptadas. Esa validación importa: la respuesta del modelo se trata como entrada externa, no como una orden que se ejecuta sin comprobar.

Para ayudar a resolver referencias como «marca esa como completada», el servicio incluye en el mensaje las tareas actuales y pide al modelo que use solamente sus IDs. El backend no decide la intención con reglas manuales sobre palabras: la decisión viene del modelo.

## Selección del modelo de Groq

La configuración usa `openai/gpt-oss-20b` mediante `GROQ_MODEL`, en vez de fijar el nombre dentro de la lógica. Los modelos y sus fechas de retiro cambian; por eso consulté la [lista oficial de modelos de Groq](https://console.groq.com/docs/models) el 23 de octubre de 2026 y confirmé que el modelo seguía apareciendo allí. También consulté la [documentación de salidas estructuradas](https://console.groq.com/docs/structured-outputs), que incluye el modelo y el formato `json_object` usado por el servicio. Esta comprobación evita depender de los modelos anteriores mencionados en el enunciado, que ya habían sido retirados.

El código solicita JSON estructurado con `response_format` y valida la respuesta, pero no se pudo hacer una petición real a Groq en este entorno: no hay un `.env` local con una API key. Por ello, la compatibilidad efectiva de una llamada en vivo debe comprobarse al configurar la clave; que el modelo aparezca en el catálogo no sustituye esa prueba.

## Configuración local

1. Instala las dependencias de Python con `uv sync`.
2. Copia `.env.example` a `.env` y añade una API key propia de Groq. Configura `GROQ_MODEL` si quieres cambiar el modelo. No compartas ni confirmes el archivo `.env`; `.gitignore` lo excluye.
3. Inicia el backend con `uv run uvicorn src.main:app --reload`.
4. En otra terminal, entra en `frontend`, instala las dependencias con `npm install` y arranca Vite con `npm run dev`.
5. Abre la dirección local que muestre Vite, permite el acceso al micrófono y prueba una instrucción hablada. También puedes escribir una transcripción en el modo manual de la interfaz.

`ALLOWED_ORIGINS` configura los orígenes que CORS permite. Debe incluir el origen local del frontend si se ejecuta en una dirección distinta de los valores predeterminados.

## Verificaciones y límites

La compilación sintáctica de los módulos Python (`python -m compileall -q src`) se completó correctamente. Para verificar el flujo de forma completa se necesita una API key válida; para probar la grabación también hacen falta un navegador con soporte de micrófono y permiso del usuario. Como las tareas viven en memoria, una lista vacía después de reiniciar el servidor es el comportamiento esperado.

El `README.md` está en la raíz. Consulté en GitHub la visibilidad del repositorio configurado en `origin` y figura como público.