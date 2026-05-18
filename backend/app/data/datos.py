# Archivo para ejecutar el proceso completo de ETL y enriquecimiento del dataset

from app.data.loader import cargar_dataset, guardar_dataset
from app.services.prediccion import enriquecer_dataset


def main():
    df = cargar_dataset()
    print("Dataset cargado con éxito. Primeros 5 registros:")
    print(df.head())
    print("-" * 50)

    df_final = enriquecer_dataset(df)

    print("Primeros 5 registros del dataset final:")
    print(df_final.head())
    print("-" * 50)

    guardar_dataset(df_final)
    print("¡Archivo final guardado en la carpeta de datos del proyecto!")


if __name__ == "__main__":
    main()
