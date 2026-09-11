"use client";

import { useCallback, useState } from "react";
import { Button, Card, Col, Container, Row } from "react-bootstrap";

import { useAlerts } from "@/entities/alert";
import { useFiles } from "@/entities/file";
import { RefreshButton } from "@/features/refresh-data";
import { UploadFileModal } from "@/features/upload-file";
import { POLL_INTERVAL_MS } from "@/shared/config/polling";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { AlertsTable } from "@/widgets/alerts-table";
import { FilesTable } from "@/widgets/files-table";

export default function Page() {
  const files = useFiles();
  // Алерты появляются в конце конвейера: опрашиваем их ровно пока есть файлы в работе.
  const alerts = useAlerts({ pollMs: files.isLive ? POLL_INTERVAL_MS : null });
  const [showUpload, setShowUpload] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const refreshAll = useCallback(() => {
    setActionError(null);
    void files.refetch();
    void alerts.refetch();
  }, [files, alerts]);

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <Card className="shadow-sm border-0 mb-4">
            <Card.Body className="p-4 d-flex justify-content-between align-items-start gap-3 flex-wrap">
              <div>
                <h1 className="h3 mb-2">Управление файлами</h1>
                <p className="text-secondary mb-0">
                  Загрузка файлов, просмотр статусов обработки и ленты алертов.
                </p>
              </div>
              <div className="d-flex gap-2">
                <RefreshButton
                  onClick={refreshAll}
                  isRefreshing={files.isRefreshing || alerts.isRefreshing}
                />
                <Button variant="primary" onClick={() => setShowUpload(true)}>
                  Добавить файл
                </Button>
              </div>
            </Card.Body>
          </Card>

          <ErrorBanner message={actionError} />

          <FilesTable query={files} onChanged={refreshAll} onError={setActionError} />
          <AlertsTable query={alerts} live={files.isLive} />
        </Col>
      </Row>

      <UploadFileModal
        show={showUpload}
        onClose={() => setShowUpload(false)}
        onUploaded={() => {
          setShowUpload(false);
          refreshAll();
        }}
      />
    </Container>
  );
}
