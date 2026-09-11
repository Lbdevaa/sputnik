"use client";

import { type FormEvent, useState } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";

import { type FileItem, uploadFile } from "@/entities/file";

type Props = {
  show: boolean;
  onClose: () => void;
  onUploaded: (file: FileItem) => void;
};

/**
 * Форма загрузки со своим состоянием и своей ошибкой (Г5): раньше ошибка отправки
 * писалась в общий баннер страницы и рисовалась за пределами открытого окна.
 */
export function UploadFileModal({ show, onClose, onUploaded }: Props) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function reset() {
    setTitle("");
    setFile(null);
    setError(null);
  }

  function close() {
    if (isSubmitting) return;
    reset();
    onClose();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = title.trim();
    if (!trimmed || !file) {
      setError("Укажите название и выберите файл");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const created = await uploadFile(trimmed, file);
      reset();
      onUploaded(created);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось загрузить файл");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal show={show} onHide={close} centered>
      <Form onSubmit={handleSubmit}>
        <Modal.Header closeButton>
          <Modal.Title>Добавить файл</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error ? <Alert variant="danger">{error}</Alert> : null}
          <Form.Group className="mb-3" controlId="upload-title">
            <Form.Label>Название</Form.Label>
            <Form.Control
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Например, Договор с подрядчиком"
              maxLength={255}
              autoFocus
            />
          </Form.Group>
          <Form.Group controlId="upload-file">
            <Form.Label>Файл</Form.Label>
            <Form.Control
              type="file"
              onChange={(event) => setFile((event.target as HTMLInputElement).files?.[0] ?? null)}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={close} disabled={isSubmitting}>
            Отмена
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? "Загрузка..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
