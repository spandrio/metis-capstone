# Imagen base de Apify con Python 3.13
FROM apify/actor-python:3.13

USER myuser

# Primero las dependencias (se cachean entre builds)
COPY --chown=myuser:myuser requirements.txt ./
RUN pip install -r requirements.txt && pip freeze

# Después el código y el modelo ya entrenado (model/)
COPY --chown=myuser:myuser . ./
RUN python -m compileall -q my_actor/

CMD ["python", "-m", "my_actor"]
