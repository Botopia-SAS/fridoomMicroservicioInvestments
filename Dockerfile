FROM python:3.9-slim

# Define el directorio de trabajo
WORKDIR /app

# Copia y instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY . .

# Expone el puerto que usará la aplicación
EXPOSE 5000

# Inicia la aplicación utilizando Gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app

