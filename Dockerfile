FROM python:3.12-slim

WORKDIR /app

COPY . .

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8765
EXPOSE 8765

CMD ["python", "-m", "src.contabil_automation.web_app"]
