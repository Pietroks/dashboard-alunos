def classificar_status(row) -> str:
    # Normaliza busca de coluna com ou sem acento
    col_contrato = "Situacao do contrato" if "Situacao do contrato" in row else "Situação do contrato"
    contrato = str(row.get(col_contrato, "")).strip().upper()

    if contrato in ["VIGENTE", "ATIVO"]:
        return "ATIVO"
    elif contrato in ["TRANCADO"]:
        return "TRANCADO"
    elif contrato in ["DESISTENTE", "DESISTENCIA", "DESISTÊNCIA"]:
        return "DESISTENTE"
    else:
        # CANCELADO, ENCERRADO, NAORENOVADO, etc.
        return "INATIVO"