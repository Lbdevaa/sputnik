import { Container, Spinner } from "react-bootstrap";

export default function Loading() {
  return (
    <Container className="d-flex justify-content-center py-5">
      <Spinner animation="border" role="status" />
    </Container>
  );
}
