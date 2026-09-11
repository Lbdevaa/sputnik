"use client";

import { Button, Spinner } from "react-bootstrap";

type Props = {
  onClick: () => void;
  isRefreshing: boolean;
};

export function RefreshButton({ onClick, isRefreshing }: Props) {
  return (
    <Button variant="outline-secondary" onClick={onClick} disabled={isRefreshing}>
      {isRefreshing ? <Spinner size="sm" animation="border" className="me-2" /> : null}
      Обновить
    </Button>
  );
}
