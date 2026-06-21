FROM node:20-alpine
WORKDIR /app

COPY package.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

ENV NODE_ENV=production
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
