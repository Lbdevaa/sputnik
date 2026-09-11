import { Alert } from "react-bootstrap";

type Props = {
  message: string | null;
  onRetry?: () => void;
};

export function ErrorBanner({ message, onRetry }: Props) {
  if (!message) return null;
  return (
    <Alert variant="danger" className="shadow-sm d-flex justify-content-between align-items-center">
      <span>{message}</span>
      {onRetry ? (
        <Alert.Link as="button" type="button" className="btn btn-link p-0" onClick={onRetry}>
          Повторить
        </Alert.Link>
      ) : null}
    </Alert>
  );
}
