import React from "react";
import FaviconUSS from "../../../public/FaviconUSS.png";

interface DashboardHeaderProps {
	email: string;
	onHelp: () => void;
	onSettings: () => void;
	onLogout: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ email, onHelp, onSettings, onLogout }) => {
	const handleLogoutClick = () => {
		if (window.confirm("¿Seguro que deseas cerrar sesión?")) {
			onLogout();
		}
	};
	// Inicial del correo
	const initial = email ? email.trim()[0].toUpperCase() : "?";
	return (
		<header style={{
			width: "100%",
			background: "#fff",
			borderBottom: "1px solid #dbe6f3",
			display: "flex",
			alignItems: "center",
			justifyContent: "space-between",
			padding: "0 32px",
			height: "70px",
			boxSizing: "border-box"
		}}>
			<div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
				<div style={{ width: 180, height: 48, background: "#285483ff", borderRadius: "16px", display: "flex", alignItems: "center", justifyContent: "flex-start", boxShadow: "0 2px 8px rgba(0,87,184,0.10)", padding: "0 18px", gap: "12px" }}>
					<img src={FaviconUSS} alt="Favicon USS" style={{ height: "32px", width: "32px", borderRadius: "8px" }} />
					<span style={{ color: "#fff", fontWeight: 800, fontSize: 24, letterSpacing: 2 }}>IA USS</span>
				</div>
				<span style={{ fontWeight: 700, fontSize: 20, color: "#285483ff" }}>Asistente IA USS</span>
			</div>
			<div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
				<span style={{ fontWeight: 600, fontSize: 16, color: "#1a3a5d", marginRight: "4px", maxWidth: "180px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{email}</span>
				<span style={{ background: "#3b98fcff", color: "#fff", borderRadius: "50%", width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 18 }}>{initial}</span>
				<button onClick={onHelp} title="Ayuda 😭 " style={{ background: "none", border: "none", cursor: "pointer" }}>
					<span style={{ fontSize: 22, color: "#285483ff" }}>?</span>
				</button>
				<button onClick={onSettings} title="Configuración" style={{ background: "none", border: "none", cursor: "pointer" }}>
					<span style={{ fontSize: 22, color: "#285483ff" }}>&#9881;</span>
				</button>
				<button onClick={handleLogoutClick} title="Salir" style={{ background: "none", border: "none", cursor: "pointer" }}>
					<span style={{ fontSize: 22, color: "#285483ff" }}>&#8594;</span>
				</button>
			</div>
		</header>
	);
};

export default DashboardHeader;
