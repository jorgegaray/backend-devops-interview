# Notes

## Developer experience
Se  dockeriza la app web y la db para una instalacion más fácil y un mayor control del entorno de trabajo
A futuro se podria tener una db con data, disponible para descargar y así evitar la ejecución del seed, dado que toma varios minutos

## Performance
En general hay varios problemas comunes entre los endpoints:
Falta de paginación lo que satura la db por la cantidad de data que se maneja (overfetching)
Falta de precarga de relaciones, conocido problema de n+1, siempre hay que minimizar lo más posible las llamadas a db y la cantidad de datos que se traen (ir a db es muy costoso)
Falta de indices lo que provoca barrido completo a las tablas (fullscan)

GET /api/posts
Se aplica paginación, demarcando un limite máximo por pagina y número de pagina minima
Se realiza precarga de relaciones (author y tags), es probable que los tags se repitan entre posts, además estoy asumiendo que los posts tienen una baja cantidad de tags, si no se tendria que pensar en una paginación para evitar la sobrecarga
Se podria buscar limitar las columnas que traemos de cada tabla, tanto para post, user y tag, dado que actualmente se genera un select con todas sus columnas, pero por ejemplo el updated_at se trae desde la tabla post pero no se utiliza, lo mismo ocurre con varias columnas del modelo user, provocando movimiento de data innecesario

GET /api/posts/{post_id}
Se soluciona problema de race condition al incrementar el view_count, se delega a postgres el cual serializa las modificaciones sobre esa fila.
Se realiza precarga de relaciones y se limita la cantidad de comments a cargar, dejando solo en 10, se asume que el front puede llamar a la siguiente pagina de comentarios si el usuario lo necesita

GET /api/posts/search/search?q=
No aplique cambios, pero dada la busqueda que se realiza sobre 2 columnas de texto se deberia implementar un indice para acelerar su busqueda y evitar un fullscan sobre la tabla, en postgres nos podria servir usar GIN + pg_trgm que es una combinación de una estructura de índice de postgres y una extensión para acelerar búsquedas de texto parciales y por similitud, la he usado antes dando muy buenos resultados.
Aplicar paginación y precarga de relaciones.

POST /api/posts
Se asume que son pocos tags y que la columna slug tiene un indice
Se evita la consulta para ir a buscar 1 a 1 cada tag
Se evita el insert 1 a 1 por cada tag
Quedando en un solo select para ir a buscar todos los tags y un solo insert para guardar los tags asociados al post


## Production readiness

Se genera un pipeline de validación automática que corre cada vez que haces push al repositorio.
Realiza un setup, instala dependencias, chequeo de seguridad, chequeo de reglas de estilo y test
Se genera un propuesta inicial de configuracion para el despliegue con kubernates, se observa que actualmente la app es data intensive y bajo en computo
A futuro implementar alguna herramienta de observabilidad y monitoreo
Analizar tráfico para implementar politicas de autoescalado y desescalado de contenedores

## Extra
Si en un futuro la app sigue creciendo su estructura actual se hace poco viable y buscaria estructurarlo en modulos para mejorar su orden, legibilidad y mantenibilidad