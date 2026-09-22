import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def main():
    df = pd.read_csv("results.csv",sep=";",names=["S/P","Size","Threads","Time"])
    serial = df.loc[df["S/P"] == "S"]

    for index,row in df.iterrows():
        size = row["Size"]
        parallel_time = row["Time"]
        serial_time = serial.loc[serial.Size == size].Time.iloc[0]
        df.loc[index,"Speedup"] = serial_time/parallel_time

    fig, ax = plt.subplots(figsize=(20,10))

    for size, group in df.groupby("Size"):
        group.plot(x="Threads",y="Speedup",ax=ax,label=size,marker='o')

    plt.ylabel("Speedup")
    plt.grid(True)

    plt.xlim(0,40*1.05)
    plt.ylim(0,df.Speedup.max()*1.05)
    ax.set_xticks(range(1,40,2))
    ax.set_yticks(range(1,math.ceil(df.Speedup.max()),1))

    fig.savefig("threads_speedup.png")

    del fig, ax

    fig, ax = plt.subplots()
    heatmap_data = df.pivot(index="Threads", columns="Size", values="Speedup")
    sns.heatmap(heatmap_data,cmap="plasma")
    fig.savefig("heatmap_speedup.png")

    del fig, ax

    fig, ax = plt.subplots()
    for size, group in df.groupby("Size"):
        group.plot(x="Threads",y="Time",ax=ax,label=size,marker='o')

    plt.ylabel("Time")
    plt.grid(True)

    fig.savefig("threads_time.png")

    del fig, ax

    fig, ax = plt.subplots()

    s = df.loc[df["S/P"] == "S"].sort_values(by="Size")

    ax.plot(s.Size,s.Time)

    fig.savefig("serial_time.png")
    
if __name__ == "__main__":
    main()
