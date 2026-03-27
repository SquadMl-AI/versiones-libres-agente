import { useEffect, useState } from "react";
import { Drawer, Popover } from "antd";
import env from "../config/enviroment";
import "../setup-pdf";
import { Viewer, Worker } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";

export default function MessageIA({ text, isLoading, response }) {
  const [sources, setSources] = useState([]);
  const [openDocument, setOpenDocument] = useState({
    isDrawerOpen: false,
    document: null,
    urlPDF: "",
  });
  const [targetPage, setTargetPage] = useState(0);

  useEffect(() => {
    if (response) {
      setSources(response?.sources ?? []);
    }
  }, [response]);

  function handleClickDocument(document) {
    let page =
      Array.isArray(document?.page_number) && document.page_number.length > 0
        ? document.page_number[0] - 1
        : 0;
    setTargetPage(page);
    setOpenDocument({
      isDrawerOpen: true,
      document,
      urlPDF: document.bloque.includes("https://")
        ? document.bloque
        : env.URL_BLOB +
          document.bloque +
          "/" +
          document.document_name +
          env.BLOB_TOKEN,
    });
  }

  // Función que reemplaza IDs por Popover
  const renderWithPopovers = (text) => {
    if (!sources.length) return text;

    let parts = [text];
    sources.forEach(({ id, content, document_name, ...rest }) => {
      const newParts = [];

      parts.forEach((part, partIndex) => {
        // Solo procesar si el fragmento es texto plano
        if (typeof part === "string") {
          const splitById = part.split(id);
          // Reconstruir intercalando el Popover
          splitById.forEach((chunk, i) => {
            newParts.push(chunk);
            if (i < splitById.length - 1) {
              // Insertar Popover entre cada aparición del ID
              newParts.push(
                <Popover
                  getPopupContainer={() =>
                    document.getElementById("fullscreen-wrapper")
                  }
                  key={`${id}-${partIndex}-${i}`}
                  content={
                    <div style={{ width: "300px" }}>
                      <div
                        style={{
                          width: "100%",
                          maxHeight: "300px",
                          overflowY: "auto",
                        }}
                      >
                        <p style={{ padding: "0px 16px" }}>{content}</p>
                        <p style={{ padding: "0px 16px" }}>
                          Páginas: {rest.page_number?.join(", ")}
                        </p>
                      </div>
                      <button
                        className="button-document flex flex-row gap-2 items-center"
                        style={{ textWrap: "wrap" }}
                        onClick={() => {
                          handleClickDocument({
                            id,
                            content,
                            document_name,
                            ...rest,
                          });
                        }}
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                          stroke="currentColor"
                          className="size-6"
                          width={24}
                          height={24}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                          />
                        </svg>
                        <span>{document_name}</span>
                      </button>
                    </div>
                  }
                  trigger="hover"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="size-6"
                    width={24}
                    height={24}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
                    />
                  </svg>
                </Popover>
              );
            }
          });
        } else {
          // Si ya es un React node (otro popover), lo dejamos igual
          newParts.push(part);
        }
      });

      parts = newParts;
    });

    return parts.flatMap((part, index) => {
      if (typeof part === "string") {
        const lines = part.split("\n");

        return lines.flatMap((line, i) => {
          const boldSplit = line.split(/(\*\*.*?\*\*)/); // Detecta fragmentos entre **

          const parsedLine = boldSplit.map((fragment, j) => {
            if (fragment.startsWith("**") && fragment.endsWith("**")) {
              return (
                <strong key={`bold-${index}-${i}-${j}`}>
                  {fragment.slice(2, -2)}
                </strong>
              );
            }
            return <span key={`span-${index}-${i}-${j}`}>{fragment}</span>;
          });

          return [
            ...parsedLine,
            i < lines.length - 1 ? <br key={`br-${index}-${i}`} /> : null,
          ];
        });
      }

      return [part];
    });
  };

  return (
    <>
      <Drawer
        title={`Vista previa: ${openDocument?.document?.document_name ?? ""}`}
        closable
        onClose={() => {
          setOpenDocument({
            isDrawerOpen: false,
            document: null,
            urlPDF: null,
          });
          setTargetPage(0);
        }}
        open={openDocument.isDrawerOpen}
        width={"50%"}
        getContainer={() => document.getElementById("fullscreen-wrapper")}
      >
        <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
          {openDocument.urlPDF && (
            <Viewer fileUrl={openDocument?.urlPDF} initialPage={targetPage} />
          )}
        </Worker>
      </Drawer>

      <div className="ia-response text-base leading-relaxed">
        {isLoading ? (
          <span className="animate-pulse text-gray-400">...</span>
        ) : (
          renderWithPopovers(text)
        )}
      </div>
    </>
  );
}
