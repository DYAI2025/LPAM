# Tailscale setup

Tailscale is the private network joining your Mac and VPS, so the SSH tunnel and
the VPS→Mac embedding calls work without exposing ports to the public internet.

## Install + join (both machines)
1. Install Tailscale: https://tailscale.com/download (macOS app; Linux: `curl -fsSL https://tailscale.com/install.sh | sh`).
2. Authenticate both into the **same tailnet**:
   - VPS: `sudo tailscale up`
   - Mac: launch the app and log in (same account).
3. Find the names/IPs: `tailscale status` — note the VPS's tailnet hostname
   (e.g. `srv1308064`) and its `100.x.y.z` IP.

## Wire it into the kit
- **SSH alias:** append `local/ssh-config-snippet` to `~/.ssh/config` and set
  `HostName` to the VPS's tailnet name or `100.x.y.z`. Test: `ssh hermes-brain hostname`.
- **VPS → Mac embeddings:** in `vps/systemd/lpam-backend.service.d/10-embedder.conf`
  set `OLLAMA_BASE_URL=http://<MAC_TAILNET_IP>:11434/v1`, then
  `systemctl daemon-reload && systemctl restart lpam-backend`.
- The Mac's `com.hermes.ollama-tailnet` LaunchAgent already binds Ollama to
  `0.0.0.0:11434`, reachable over the tailnet.

## Notes / traps
- **Public VPS IP works too** but loses the private-network benefit; prefer the
  tailnet IP/host in the ssh alias.
- **IPv6 / `-L` binding:** the tunnel scripts bind `127.0.0.1` explicitly to avoid
  IPv6 surprises.
- Use `IdentitiesOnly yes` (in the ssh snippet) so SSH doesn't offer the wrong key.
- Keep the dashboard on `127.0.0.1:9119` on the VPS — only the tunnel (over the
  tailnet) reaches it; it is never bound to a public interface.
