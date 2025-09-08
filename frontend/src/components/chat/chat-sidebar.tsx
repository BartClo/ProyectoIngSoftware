import React, { useState } from "react";
import LapizIcon from "../../assets/Lapiz.svg";
import BasureroIcon from "../../assets/Basurero.svg";
import ChatIcon from "../../assets/chat.svg";

interface Conversation {
	id: string;
	name: string;
	createdAt: string;
}

const initialConversations: Conversation[] = [
	{
		id: "1",
		name: "Nueva conversación",
		createdAt: new Date().toLocaleDateString(),
	},
];

const ChatSidebar: React.FC<{
	activeId: string;
	onSelect: (id: string) => void;
}> = ({ activeId, onSelect }) => {
	const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
		const [menuId, setMenuId] = useState<string | null>(null);
		const [renameId, setRenameId] = useState<string | null>(null);
		const [newName, setNewName] = useState("");

		const handleNewConversation = () => {
			const newConv: Conversation = {
				id: Date.now().toString(),
				name: "Nueva conversación",
				createdAt: new Date().toLocaleDateString(),
			};
			setConversations([newConv, ...conversations]);
			onSelect(newConv.id);
		};

		const handleDelete = (id: string) => {
			if (window.confirm("¿Estás seguro que deseas eliminar esta conversación?")) {
				setConversations(conversations.filter((c) => c.id !== id));
				if (activeId === id && conversations.length > 1) {
					onSelect(conversations[0].id);
				}
			}
		};

		const handleRename = (id: string) => {
			setConversations(
				conversations.map((c) =>
					c.id === id ? { ...c, name: newName || c.name } : c
				)
			);
			setRenameId(null);
			setNewName("");
			setMenuId(null);
		};

	return (
			<aside style={{
				width: "260px",
				background: "#e3f0ff",
				borderRight: "2px solid #b3d4fc",
				padding: "24px 12px",
				height: "100vh",
				boxSizing: "border-box",
				display: "flex",
				flexDirection: "column",
				gap: "16px"
			}}>
						<button onClick={handleNewConversation} style={{
							background: "#0057b8",
							color: "#fff",
							border: "none",
							borderRadius: "8px",
							padding: "10px",
							fontWeight: 600,
							cursor: "pointer",
							marginBottom: "12px",
							boxShadow: "0 2px 8px rgba(0,87,184,0.08)"
						}}>+ Nueva conversación</button>
						<hr style={{ border: "none", borderTop: "1px solid #b3d4fc", margin: "8px 0 16px 0" }} />
						<div style={{ flex: 1, overflowY: "auto" }}>
							{conversations.map((conv) => (
															<div key={conv.id} style={{
																background: activeId === conv.id ? "#0057b8" : "#fff",
																color: activeId === conv.id ? "#fff" : "#222",
																borderRadius: "8px",
																padding: "10px",
																marginBottom: "8px",
																display: "flex",
																alignItems: "center",
																justifyContent: "space-between",
																boxShadow: activeId === conv.id ? "0 2px 8px rgba(0,87,184,0.10)" : "0 1px 4px rgba(0,0,0,0.04)",
																border: activeId === conv.id ? "2px solid #b3d4fc" : "1px solid #e3f0ff",
																position: "relative"
															}}>
																			<span style={{ display: "flex", alignItems: "center", marginRight: "10px" }}>
																				<img src={ChatIcon} alt="Chat" style={{ width: "22px", height: "22px" }} />
																			</span>
																<div onClick={() => onSelect(conv.id)} style={{ cursor: "pointer", flex: 1, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>
																	<strong style={{ overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis", display: "block" }}>{conv.name}</strong>
																	<div style={{ fontSize: "12px", color: activeId === conv.id ? "#e3f0ff" : "#888" }}>{conv.createdAt}</div>
																</div>
																<div style={{ position: "relative" }}>
														<button
															onClick={() => setMenuId(menuId === conv.id ? null : conv.id)}
															style={{ background: "none", border: "none", color: activeId === conv.id ? "#fff" : "#0057b8", fontSize: "20px", cursor: "pointer", padding: "0 6px" }}
															title="Opciones"
														>&#8942;</button>
														{menuId === conv.id && (
															<div style={{ position: "absolute", top: "28px", right: "0", background: "#fff", border: "1px solid #b3d4fc", borderRadius: "8px", boxShadow: "0 2px 8px rgba(0,87,184,0.10)", zIndex: 10, minWidth: "120px" }}>
																					<button onClick={() => { setRenameId(conv.id); setMenuId(null); setNewName(conv.name); }} style={{ display: "flex", alignItems: "center", width: "100%", background: "none", border: "none", color: "#0057b8", padding: "10px", textAlign: "left", cursor: "pointer" }}>
																						<img src={LapizIcon} alt="Renombrar" style={{ width: "18px", height: "18px", marginRight: "8px" }} />
																						Renombrar
																					</button>
																					<button onClick={() => handleDelete(conv.id)} style={{ display: "flex", alignItems: "center", width: "100%", background: "none", border: "none", color: "#d32f2f", padding: "10px", textAlign: "left", cursor: "pointer" }}>
																						<img src={BasureroIcon} alt="Eliminar" style={{ width: "18px", height: "18px", marginRight: "8px" }} />
																						Eliminar
																					</button>
															</div>
														)}
																						{renameId === conv.id && (
																							<div style={{ position: "absolute", top: "28px", right: "0", background: "#fff", border: "1px solid #b3d4fc", borderRadius: "8px", boxShadow: "0 2px 8px rgba(0,87,184,0.10)", zIndex: 10, minWidth: "180px", maxWidth: "220px", padding: "12px", boxSizing: "border-box" }}>
																								<input
																									value={newName}
																									onChange={e => setNewName(e.target.value)}
																									style={{ width: "100%", borderRadius: "6px", border: "1px solid #b3d4fc", padding: "8px", marginBottom: "8px", background: "#fff", color: "#222", fontSize: "15px", boxSizing: "border-box", overflow: "hidden" }}
																									autoFocus
																									placeholder="Nombre"
																									maxLength={32}
																								/>
																								<button onClick={() => handleRename(conv.id)} style={{ background: "#e3f0ff", color: "#0057b8", border: "none", borderRadius: "6px", padding: "6px 10px", marginRight: "6px" }}>Guardar</button>
																								<button onClick={() => { setRenameId(null); setNewName(""); }} style={{ background: "#fff", color: "#0057b8", border: "none", borderRadius: "6px", padding: "6px 10px" }}>Cancelar</button>
																							</div>
																						)}
													</div>
												</div>
					))}
				</div>
			</aside>
	);
};

export default ChatSidebar;
