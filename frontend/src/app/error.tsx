"use client";

import { Alert, Button, Container } from "react-bootstrap";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: Props) {
  return (
    <Container className="py-5">
      <Alert variant="danger">
        <Alert.Heading>Что-то пошло не так</Alert.Heading>
        <p className="mb-3">{error.message || "Неизвестная ошибка"}</p>
        <Button variant="outline-danger" onClick={reset}>
          Попробовать снова
        </Button>
      </Alert>
    </Container>
  );
}
