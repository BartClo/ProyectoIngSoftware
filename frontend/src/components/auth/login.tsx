
import React, { useState } from "react";
import FondoUSS from "../../assets/FondoUSS.svg";
import LogoUSS from "../../assets/LogoUSS.svg";

interface LoginProps {
	onLoginSuccess?: (email: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");

	const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setEmail(e.target.value);
		setError("");
	};

	const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setPassword(e.target.value);
	};

	const validateEmail = (email: string) => {
		return /.+@docente\.uss\.cl$/.test(email);
	};

		const handleSubmit = (e: React.FormEvent) => {
			e.preventDefault();
			if (!validateEmail(email)) {
				setError("El correo debe terminar en @docente.uss.cl");
				return;
			}
			// Aquí iría la lógica de autenticación
			if (onLoginSuccess) onLoginSuccess(email);
		};

	return (
			<div
				style={{
					minHeight: "100vh",
					width: "100vw",
					overflow: "hidden",
					backgroundImage: `url(${FondoUSS})`,
					backgroundSize: "cover",
					backgroundPosition: "center",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
				}}
			>
						<div
							style={{
								background: "rgba(255,255,255,0.97)",
								borderRadius: "32px",
								boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
								padding: "40px 32px",
								maxWidth: "400px",
								width: "100%",
								textAlign: "center",
								minWidth: "320px",
								display: "flex",
								flexDirection: "column",
								alignItems: "center",
							}}
						>
									<img src={LogoUSS} alt="Logo USS" style={{ width: "120px", margin: "0 auto 24px", display: "block" }} />
									<h1 style={{ fontWeight: 800, fontSize: "2rem", marginBottom: "10px", color: "#0057b8" }}>Asistente IA</h1>
									<p style={{ marginBottom: "24px", color: "#555", fontSize: "1.1rem" }}>
										Inicie sesión con su cuenta institucional
									</p>
									<form onSubmit={handleSubmit} autoComplete="off" style={{ width: "100%" }}>
								<div style={{ marginBottom: "16px", textAlign: "left" }}>
									<label htmlFor="email" style={{ fontWeight: 500, color: '#111' }}>Correo electrónico</label>
									<input
										id="email"
										type="email"
										value={email}
										onChange={handleEmailChange}
										placeholder="usuario@docente.uss.cl"
										style={{
											width: "100%",
											padding: "10px",
											borderRadius: "12px",
											border: "1px solid #ccc",
											marginTop: "6px",
											fontSize: "16px",
											background: "#fff",
											color: "#111",
											boxSizing: "border-box",
										}}
										required
									/>
								</div>
								<div style={{ marginBottom: "16px", textAlign: "left" }}>
									<label htmlFor="password" style={{ fontWeight: 500, color: '#111' }}>Contraseña</label>
									<input
										id="password"
										type="password"
										value={password}
										onChange={handlePasswordChange}
										placeholder="Ingrese su contraseña"
										style={{
											width: "100%",
											padding: "10px",
											borderRadius: "12px",
											border: "1px solid #ccc",
											marginTop: "6px",
											fontSize: "16px",
											background: "#fff",
											color: "#111",
											boxSizing: "border-box",
										}}
										required
									/>
								</div>
								{error && (
									<div style={{ color: "#d32f2f", marginBottom: "12px" }}>{error}</div>
								)}
								<button
									type="submit"
									style={{
										width: "100%",
										padding: "12px",
										background: "#0057b8",
										color: "#fff",
										border: "none",
										borderRadius: "12px",
										fontWeight: 600,
										fontSize: "16px",
										cursor: "pointer",
										marginTop: "8px",
									}}
								>
									Iniciar sesión
								</button>
							</form>
						</div>
			</div>
	);
};

export default Login;
