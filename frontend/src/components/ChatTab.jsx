import { useState, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { fetchData } from "../api";
import MessageIA from "./MessageIA";
import { Select } from "antd";

// Forzar uso de 'motion' para evitar warning de no-unused-vars
const Motion = motion;

export default function ChatTab({
  access,
  message,
  setMessage,
  messages,
  setMessages,
  setSelectedValue,
  selectedValue,
}) {
  const iframeRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleEnterFullscreen = () => {
    const element = iframeRef.current;
    if (element) {
      if (element.requestFullscreen) {
        element.requestFullscreen();
      } else if (element.mozRequestFullScreen) {
        /* Firefox */
        element.mozRequestFullScreen();
      } else if (element.webkitRequestFullscreen) {
        /* Chrome, Safari & Opera */
        element.webkitRequestFullscreen();
      } else if (element.msRequestFullscreen) {
        /* IE/Edge */
        element.msRequestFullscreen();
      }
    }
  };

  const handleExitFullscreen = () => {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) {
      /* Firefox */
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
      /* Chrome, Safari & Opera */
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      /* IE/Edge */
      document.msExitFullscreen();
    }
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      handleEnterFullscreen();
    } else {
      handleExitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
    document.addEventListener("mozfullscreenchange", handleFullscreenChange);
    document.addEventListener("MSFullscreenChange", handleFullscreenChange);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener(
        "webkitfullscreenchange",
        handleFullscreenChange
      );
      document.removeEventListener(
        "mozfullscreenchange",
        handleFullscreenChange
      );
      document.removeEventListener(
        "MSFullscreenChange",
        handleFullscreenChange
      );
    };
  }, []);

  const [isLoading, setIsLoading] = useState(false);

  function sendMsg(indexMessageError = null) {
    const email = sessionStorage.getItem("userEmail");
    if (isLoading) return;
    setIsLoading(true);
    let userMessageText = message;

    // Si se pasó un índice de error, extraer el mensaje original y eliminarlo
    if (indexMessageError !== null) {
      userMessageText = messages[indexMessageError].text; // Sobrescribe message
      setMessages((prev) => {
        const sinMensajeError = prev.filter((_, i) => i !== indexMessageError);

        return [
          ...sinMensajeError,
          {
            id: sinMensajeError.length + 1,
            text: userMessageText,
            sender: "user",
          },
          {
            id: sinMensajeError.length + 2,
            text: "",
            sender: "bot",
            isLoading: true,
            isError: false,
          },
        ];
      });
    } else {
      // Mensaje normal desde input
      setMessages((prev) => [
        ...prev,
        { id: prev.length + 1, text: userMessageText, sender: "user" },
        {
          id: prev.length + 2,
          text: "",
          sender: "bot",
          isLoading: true,
          isError: false,
          indexType:
            selectedValue === "index_sentencias"
              ? "Sentencias"
              : "Versiones Libres",
        },
      ]);
      setMessage("");
    }

    fetchData({
      url:
        selectedValue == "index_sentencias"
          ? "/chat_ask/chat_ask_sentencias"
          : "/chat_ask/chat_ask_audiencias",
      method: "POST",
      body: {
        query: userMessageText,
        user_email: email,
        index: selectedValue,
      },
    })
      .then((res) => {
        setMessages((prev) =>
          prev.map((msg, index) =>
            index === prev.length - 1
              ? {
                  ...msg,
                  isLoading: false,
                  text: res.response.answer,
                  response: res.response,
                  message_id: res.message_id,
                  stateFeed: 0,
                }
              : msg
          )
        );
      })
      .catch(() => {
        setMessages((prev) => {
          const updated = prev.map((msg, index) =>
            index === prev.length - 2
              ? { ...msg, isLoading: false, isError: true }
              : msg
          );
          return updated.slice(0, -1); // Elimina el mensaje "bot" que está isLoading
        });
      })
      .finally(() => {
        setIsLoading(false);
      });
  }

  function handleOnSubmit(event) {
    event.preventDefault();
    sendMsg();
  }

  const handleChange = (value) => {
    setSelectedValue(value);
  };

  const [availableOptions, setAvailableOptions] = useState([]);

  useEffect(() => {
    if (access && Array.isArray(access)) {
      const opts = [];

      if (access.includes("sentencias")) {
        opts.push({ label: "Sentencias", value: "index_sentencias" });
      }

      if (access.includes("audiencias")) {
        opts.push({ label: "Versiones Libres", value: "index_audiencias" });
      }

      setAvailableOptions(opts);

      // Set default value
      if (access.includes("sentencias")) {
        setSelectedValue("index_sentencias");
      } else if (access.includes("audiencias")) {
        setSelectedValue("index_audiencias");
      } else {
        setSelectedValue(""); // No acceso
      }
    }
  }, [access, setSelectedValue]); // Añadido setSelectedValue para evitar warning

  function changeStateFeed(id, value, preValue) {
    setMessages((prevMessages) =>
      prevMessages.map((msg) =>
        msg.message_id === id ? { ...msg, stateFeed: value } : msg
      )
    );
    fetchData({
      url: "/feed_message",
      method: "PUT",
      body: { message_id: id, feed: value },
    }).catch(() => {
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.message_id === id ? { ...msg, stateFeed: preValue } : msg
        )
      );
    });
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 150px)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          marginBottom: "1rem",
          justifyContent: "space-between",
        }}
      >
        <h2>Chat</h2>
        <div>
          {availableOptions.length > 0 && (
            <Select
              style={{ width: 250, height: 40, textAlign: "left" }}
              placeholder="Filtrar por"
              value={selectedValue}
              onChange={handleChange}
              options={availableOptions} // aquí usamos el array calculado
            />
          )}
        </div>
      </div>
      <div id="fullscreen-wrapper" className="chat-container" ref={iframeRef}>
        <AnimatePresence>
          <div className="flex-1 w-full h-full overflow-y-auto flex flex-col gap-2 py-4 px-2">
            {messages.map(
              (
                {
                  id,
                  text,
                  sender,
                  isLoading,
                  isError,
                  response,
                  indexType,
                  stateFeed,
                  message_id,
                },
                index
              ) => (
                <Motion.div
                  key={id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className={`max-w-8/12 flex flex-col ${
                    sender === "bot" ? "self-start" : "self-end"
                  }`}
                >
                  {sender == "bot" && (
                    <p
                      style={{
                        textAlign: "left",
                        fontSize: "14px",
                        margin: "0",
                        padding: "0",
                      }}
                    >
                      {indexType}
                    </p>
                  )}
                  <div
                    className={`text-left flex-1  ${
                      sender === "bot" ? "bot-message" : "user-message"
                    }  ${isError ? "error-message" : ""}`}
                  >
                    <div className="message-content">
                      {sender === "bot" ? (
                        <>
                          <MessageIA
                            text={text}
                            isLoading={isLoading}
                            response={response}
                          />
                        </>
                      ) : (
                        text
                      )}
                    </div>
                  </div>
                  {sender == "bot" && stateFeed >= 0 && (
                    <div className="flex flex-row mt-2 gap-2">
                      <button
                        className={`btn-chat ${stateFeed === 1 && "active"} `}
                        onClick={() =>
                          stateFeed != 1
                            ? changeStateFeed(message_id, 1, stateFeed)
                            : null
                        }
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                          stroke="currentColor"
                          className="size-6"
                          width={20}
                          height={20}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V2.75a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m10.598-9.75H14.25M5.904 18.5c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 9.953 4.167 9.5 5 9.5h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z"
                          />
                        </svg>
                      </button>
                      <button
                        className={`btn-chat ${stateFeed === 2 && "active"} `}
                        onClick={() =>
                          stateFeed != 2
                            ? changeStateFeed(message_id, 2, stateFeed)
                            : null
                        }
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={1.5}
                          stroke="currentColor"
                          className="size-6"
                          width={20}
                          height={20}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M7.498 15.25H4.372c-1.026 0-1.945-.694-2.054-1.715a12.137 12.137 0 0 1-.068-1.285c0-2.848.992-5.464 2.649-7.521C5.287 4.247 5.886 4 6.504 4h4.016a4.5 4.5 0 0 1 1.423.23l3.114 1.04a4.5 4.5 0 0 0 1.423.23h1.294M7.498 15.25c.618 0 .991.724.725 1.282A7.471 7.471 0 0 0 7.5 19.75 2.25 2.25 0 0 0 9.75 22a.75.75 0 0 0 .75-.75v-.633c0-.573.11-1.14.322-1.672.304-.76.93-1.33 1.653-1.715a9.04 9.04 0 0 0 2.86-2.4c.498-.634 1.226-1.08 2.032-1.08h.384m-10.253 1.5H9.7m8.075-9.75c.01.05.027.1.05.148.593 1.2.925 2.55.925 3.977 0 1.487-.36 2.89-.999 4.125m.023-8.25c-.076-.365.183-.75.575-.75h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398-.306.774-1.086 1.227-1.918 1.227h-1.053c-.472 0-.745-.556-.5-.96a8.95 8.95 0 0 0 .303-.54"
                          />
                        </svg>
                      </button>
                    </div>
                  )}
                  {sender == "user" && isError && (
                    <button
                      type="button"
                      onClick={() => sendMsg(index)}
                      aria-label="Reenviar mensaje que no se pudo enviar"
                      title="Reenviar mensaje"
                      className="retry-button"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        width={16}
                        height={16}
                        viewBox="0 0 24 24"
                        strokeWidth={2.0}
                        stroke="#e44143"
                        className="size-6"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                        />
                      </svg>
                    </button>
                  )}
                </Motion.div>
              )
            )}
          </div>
        </AnimatePresence>
        <form className="content-input" onSubmit={handleOnSubmit}>
          <input
            type="text"
            name=""
            id=""
            placeholder="Escribe aquí"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <button
            type="submit"
            className="button-send"
            disabled={isLoading || message.trim().length === 0}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              width={24}
              height={24}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
              />
            </svg>
          </button>
        </form>
      </div>
      {/* <iframe
        ref={iframeRef}
        src={`http://10.1.180.15/chat/share?shared_id=ee35c5de0fc711f0b8660242ac120006&from=chat&auth=ExMGUwNDlhZWVkYTExZWZiZjVmMDI0Mm`}
        style={{ width: "100%", height: "100%", minWidth: 800, minHeight: 550, border: '1px solid black' }}
        frameBorder="0"
        title="Chat Ley 975"
        allow="fullscreen; clipboard-write; clipboard-read"
      /> */}
      <div style={{ display: "flex", alignItems: "center", marginTop: "1rem" }}>
        <button
          onClick={toggleFullscreen}
          className="tab-btn"
          style={{
            padding: "0.5rem 1rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
            backgroundColor: "#f0f0f0",
            cursor: "pointer",
          }}
        >
          {isFullscreen ? "Salir de Pantalla Completa" : "Pantalla Completa"}
        </button>
        <div style={{ fontSize: 13, color: "#888", marginLeft: "1rem" }}>
          Chat interactivo conectado a la base de datos de la Ley 975.
        </div>
      </div>
    </div>
  );
}
