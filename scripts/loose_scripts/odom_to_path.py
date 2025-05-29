import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_trajectory(csv_path):
    # Lê o CSV
    df = pd.read_csv(csv_path)

    # Verifica se as colunas necessárias existem
    required_columns = ['pose.pose.position.x', 'pose.pose.position.y', 'pose.pose.position.z']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Coluna '{col}' não encontrada no CSV.")

    # Extrai as colunas de posição
    x = df['pose.pose.position.x']
    y = df['pose.pose.position.y']
    z = df['pose.pose.position.z']

    # Plot em 2D (XY)
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, label='Trajetória XY', marker='o', markersize=2, linewidth=1)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Trajetória do Robô (XY)')
    plt.axis('equal')
    plt.grid(True)
    plt.legend()
    plt.savefig("odom.png")

    # Plot em 3D (opcional)
    try:
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(x, y, z, label='Trajetória 3D')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Trajetória do Robô em 3D')
        ax.legend()
        plt.savefig("odom3d.png")
    except ImportError:
        print("mpl_toolkits.mplot3d não está disponível para o plot 3D.")

def main():
    plot_trajectory("/home/manuela/Documents/VerLab/dataAnalysisForRobotics/lib_tests/lib_script_test/csv_files/per_run/run_0/lego_loam-odom.csv")

if __name__ == "__main__":
    main()