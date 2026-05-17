def verificar_alertas(df):
    alertas = []
    if 'sueldo pretendido' in df.columns:
        if df['sueldo pretendido'].isnull().sum() > 0:
            alertas.append('Quedan valores nulos en sueldo pretendido')
    return {"alertas": alertas}
