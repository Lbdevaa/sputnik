import type { ReactNode } from "react";
import { Badge, Card } from "react-bootstrap";

type Props = {
  title: string;
  count?: number;
  /** Индикатор фонового обновления рядом с заголовком. */
  live?: boolean;
  actions?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ title, count, live, actions, children }: Props) {
  return (
    <Card className="shadow-sm border-0 mb-4">
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center gap-3 flex-wrap">
          <div className="d-flex align-items-center gap-2">
            <h2 className="h5 mb-0">{title}</h2>
            {count !== undefined ? <Badge bg="secondary">{count}</Badge> : null}
            {live ? (
              <span className="small text-secondary" title="Обновляется автоматически">
                ● live
              </span>
            ) : null}
          </div>
          {actions}
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">{children}</Card.Body>
    </Card>
  );
}
