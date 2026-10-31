# Imagen del front: el servidor de desarrollo de Vite en el puerto 3000 (US-TECH-002).
FROM node:22-alpine

WORKDIR /app

# Primero las dependencias: si solo cambia el código, Docker reusa esta capa.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000
# --host 0.0.0.0: sin esto, Vite escucha solo adentro del contenedor y no se ve desde tu máquina.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
