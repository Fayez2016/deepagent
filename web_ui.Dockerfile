FROM docker.io/node:20-alpine
WORKDIR /app
COPY web_ui/package.json /app/package.json
RUN npm install
COPY web_ui /app
EXPOSE 3000
CMD ["npm", "run", "dev"]
