"use client";

import { useState } from "react";
import { Button } from "react-bootstrap";

import { deleteFile, type FileItem } from "@/entities/file";

type Props = {
  file: FileItem;
  onDeleted: (file: FileItem) => void;
  onError: (message: string) => void;
};

export function DeleteFileButton({ file, onDeleted, onError }: Props) {
  const [isDeleting, setIsDeleting] = useState(false);

  async function handleClick() {
    if (!window.confirm(`Удалить «${file.title}»? Вместе с файлом удалятся его алерты.`)) {
      return;
    }
    setIsDeleting(true);
    try {
      await deleteFile(file.id);
      onDeleted(file);
    } catch (caught) {
      onError(caught instanceof Error ? caught.message : "Не удалось удалить файл");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <Button variant="outline-danger" size="sm" onClick={handleClick} disabled={isDeleting}>
      {isDeleting ? "…" : "Удалить"}
    </Button>
  );
}
