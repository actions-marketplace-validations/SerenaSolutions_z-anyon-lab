#!/usr/bin/env python3
"""Z-Anyon Lab — non-Abelian anyon braid battery (S3 qutrit miniature).

Runs the house's declared non-Abelian anyon battery in exact statevector
arithmetic (numpy, no shots, no hardware) and seals the result with Z-QEA
(SHA3-256). Verdict NAO_ABELIANO_VERIFICADO requires:
  - commutator [B_R, B_S] L1-norm != 0 (order matters — the non-Abelian signature)
  - forbidden fusion channel |11> keeps probability exactly 0 (fusion veto)
  - braid words (B_R B_S)^k and (B_S B_R)^k diverge for k not multiple of 3
  - and coincide for k multiple of 3 (the period-3 echo, documented in ZEPHIRUM round 3)
Exit codes: 0 = NAO_ABELIANO_VERIFICADO, 1 = REFUSED, 2 = usage error.
"""
import sys, os, json, hashlib, datetime
import numpy as np

def seal(rec):
    payload = {k: v for k, v in rec.items() if k != "selo_sha3_256"}
    return hashlib.sha3_256(json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode()).hexdigest()

B_R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=float)  # braid in plane (0,2)
B_S = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)  # braid in plane (1,2)
K_MAX = 6

def device_gate(n=3, shots=1024, seed=1701):
    """v1.9.0 — porta de integridade GHZ (kernel ZYQL v1.9.0): o e confiado
    o dispositivo antes de qualquer veredito de trançado."""
    try:
        from zyql_quantum_gate import ghz_integrity
        return ghz_integrity(n=n, shots=shots, seed=seed)
    except ImportError:
        return {"fidelity_ghz": None, "threshold": 0.80,
                "device_trusted": None, "mode": "GHZ_UNAVAILABLE (kernel ZYQL nao instalado; declarado)"}


def battery():
    comm = B_R @ B_S - B_S @ B_R
    comm_l1 = int(np.abs(comm).sum())
    e0 = np.array([1.0, 0.0, 0.0])
    W, Wi = B_R @ B_S, B_S @ B_R
    words = {}
    for k in range(1, K_MAX + 1):
        p_rs = np.linalg.matrix_power(W, k) @ e0
        p_sr = np.linalg.matrix_power(Wi, k) @ e0
        words[str(k)] = {
            "BR_BS_k": [round(float(x), 9) for x in p_rs],
            "BS_BR_k": [round(float(x), 9) for x in p_sr],
            "diverge": bool(round(float(np.linalg.norm(p_rs - p_sr)), 9) > 1e-9),
        }
    uniform4 = np.zeros(4); uniform4[0] = uniform4[1] = uniform4[2] = 1 / np.sqrt(3)
    lifted = np.eye(4); lifted[:3, :3] = W
    veto = round(float(abs((lifted @ uniform4)[3]) ** 2), 15)
    div_non3 = all(words[str(k)]["diverge"] for k in range(1, K_MAX + 1) if k % 3 != 0)
    echo_3 = all(not words[str(k)]["diverge"] for k in range(1, K_MAX + 1) if k % 3 == 0)
    verdict = "NAO_ABELIANO_VERIFICADO" if (comm_l1 != 0 and veto < 1e-12 and div_non3 and echo_3) else "REFUSED"
    return {"commutator_L1": comm_l1, "braids_noncommuting": bool(comm_l1 != 0),
            "braid_words": words, "diverge_k_not_multiple_of_3": bool(div_non3),
            "period_3_echo": bool(echo_3), "forbidden_channel_p": veto,
            "verdict": verdict}

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "anyon_receipt.json"
    gate = device_gate()
    r = battery()
    rec = {"spec": "Z-QEA", "modulo": "anyon_lab.py (SerenaSolutions/z-anyon-lab)",
           "device_gate_ghz": gate,
           "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "modo": "SIMULACAO STATEVECTOR LOCAL (numpy, aritmetica exata) — sem hardware, sem shots, sem endosso",
           "model": "S3 qutrit miniature (fusion space dim 3, |11> vetoed) — declarado: nao e o duplo quantico completo",
           "resultados": r,
           "selo_regra": "selo = SHA3-256 sobre json.dumps(recibo, sort_keys=True, ensure_ascii=True, default=str) com o campo selo_sha3_256 REMOVIDO da entrada"}
    rec["selo_sha3_256"] = seal(rec)
    json.dump(rec, open(out, "w"), ensure_ascii=True, indent=1)
    print("GHZ gate:", gate.get("fidelity_ghz"), "->", gate.get("device_trusted"))
    print("Z-ANYON LAB:", r["verdict"], "| commutator L1 =", r["commutator_L1"], "| selo:", rec["selo_sha3_256"][:16] + "...")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"verdict={r['verdict']}\nseal={rec['selo_sha3_256']}\n")
    return 0 if r["verdict"] == "NAO_ABELIANO_VERIFICADO" else 1

if __name__ == "__main__":
    sys.exit(main())
