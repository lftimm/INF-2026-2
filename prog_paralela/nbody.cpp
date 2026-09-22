#include <cmath>
#include <cstring>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include <omp.h>

/*
Programação Paralela
simulação de n corpos - Lucas Timm 00323696

lê um arquivo CSV com uma configuração inicial de planetas
roda versões seriais e paralelas do programa
printa o resultado para a tela em formato csv
*/

struct Universe {
  int size;
  std::vector<float> x{};
  std::vector<float> y{};
  std::vector<float> z{};
  std::vector<float> fx{};
  std::vector<float> fy{};
  std::vector<float> fz{};
  std::vector<float> vx{};
  std::vector<float> vy{};
  std::vector<float> vz{};
};

Universe create_universe(std::string_view ss) {
  std::ifstream fs{ss.data()};

  Universe uni{};

  std::string planet;

  int i{};
  for (; std::getline(fs, planet); i++) {
    std::stringstream ss{planet};
    std::string value{};

    std::getline(ss, value, ';');
    uni.x.push_back(std::stof(value));

    std::getline(ss, value, ';');
    uni.y.push_back(std::stof(value));

    std::getline(ss, value, ';');
    uni.z.push_back(std::stof(value));
  }

  fs.close();

  uni.vx.resize(i);
  uni.vy.resize(i);
  uni.vz.resize(i);

  uni.x.resize(i);
  uni.y.resize(i);
  uni.z.resize(i);

  uni.fx.resize(i);
  uni.fy.resize(i);
  uni.fz.resize(i);

  uni.x.shrink_to_fit();
  uni.y.shrink_to_fit();
  uni.z.shrink_to_fit();

  uni.fx.shrink_to_fit();
  uni.fy.shrink_to_fit();
  uni.fz.shrink_to_fit();

  uni.size = i;
  return uni;
};

inline void parallel_simulation(Universe &universe, const float dt) {

#pragma omp parallel shared(universe, dt)
  {
#pragma omp for
    for (int i = 0; i < universe.size; i++) {
      const float &x = universe.x[i];
      const float &y = universe.y[i];
      const float &z = universe.z[i];

      float &fx = universe.fx[i];
      float &fy = universe.fy[i];
      float &fz = universe.fz[i];

      for (int j = 0; j < universe.size; j++) {

        if (j == i)
          continue;

        const float dx = universe.x[j] - x;
        const float dy = universe.y[j] - y;
        const float dz = universe.z[j] - z;

        const float dist_sq = dx * dx + dy * dy + dz * dz;

        const float inv_dist = 1.0f / std::sqrt(dist_sq);
        const float inv_dist_cubed = inv_dist * inv_dist * inv_dist;

        const float force_x = dx * inv_dist_cubed;
        const float force_y = dy * inv_dist_cubed;
        const float force_z = dz * inv_dist_cubed;

        fx += force_x;
        fy += force_y;
        fz += force_y;
      }
    }

#pragma omp barrier

#pragma omp for simd
    for (int i = 0; i < universe.size; i++) {
      universe.x[i] += universe.vx[i] * dt + 0.5f * universe.fx[i] * dt * dt;
      universe.y[i] += universe.vy[i] * dt + 0.5f * universe.fy[i] * dt * dt;
      universe.z[i] += universe.vz[i] * dt + 0.5f * universe.fz[i] * dt * dt;

      universe.vx[i] += universe.fx[i] * dt;
      universe.vy[i] += universe.fy[i] * dt;
      universe.vz[i] += universe.fz[i] * dt;

      universe.fx[i] = 0.0f;
      universe.fy[i] = 0.0f;
      universe.fz[i] = 0.0f;
    }
  }
}

inline void serial_simulation(Universe &universe, float dt) {
  for (int i = 0; i < universe.size; i++) {
    const float &x = universe.x[i];
    const float &y = universe.y[i];
    const float &z = universe.z[i];

    float &fx = universe.fx[i];
    float &fy = universe.fy[i];
    float &fz = universe.fz[i];

#pragma omp simd
    for (int j = i + 1; j < universe.size; j++) {
      const float dx = universe.x[j] - x;
      const float dy = universe.y[j] - y;
      const float dz = universe.z[j] - z;

      const float dist_sq = dx * dx + dy * dy + dz * dz;

      const float inv_dist = 1.0f / std::sqrt(dist_sq);
      const float inv_dist_cubed = inv_dist * inv_dist * inv_dist;

      const float force_x = dx * inv_dist_cubed;
      const float force_y = dy * inv_dist_cubed;
      const float force_z = dz * inv_dist_cubed;

      fx += force_x;
      fy += force_y;
      fz += force_z;

      universe.fx[j] -= force_x;
      universe.fy[j] -= force_y;
      universe.fz[j] -= force_z;
    }
  }

#pragma omp simd
  for (int i = 0; i < universe.size; i++) {
    universe.x[i] += universe.vx[i] * dt + 0.5f * universe.fx[i] * dt * dt;
    universe.y[i] += universe.vy[i] * dt + 0.5f * universe.fy[i] * dt * dt;
    universe.z[i] += universe.vz[i] * dt + 0.5f * universe.fz[i] * dt * dt;

    universe.vx[i] += universe.fx[i] * dt;
    universe.vy[i] += universe.fy[i] * dt;
    universe.vz[i] += universe.fz[i] * dt;

    universe.fx[i] = 0.0f;
    universe.fy[i] = 0.0f;
    universe.fz[i] = 0.0f;
  }
}

double run_simulation(Universe &universe, float dt,
                      std::function<void(Universe &, float)> sim) {
  double t0{omp_get_wtime()};
  int total_steps(std::ceil(1 / dt));
  for (int it = 0; it < total_steps; it++) {
    sim(universe, dt);
  }
  double t1{omp_get_wtime()};

  return t1 - t0;
}

int main(int argc, char **argv) {

  const float dt{0.0001};
  const float simulation_time{1.0f};
  const int total_steps = 1 / dt;

  if (argc != 3) {
    std::cerr << "usage: [program] -p or -s initial_state.csv\n";
    return 1;
  }

  bool execute_serial{!std::strcmp(argv[1], "-s")};
  Universe universe{create_universe(argv[2])};

  std::function<void(Universe &, float)> sim{
      execute_serial ? serial_simulation : parallel_simulation
  };

  double elapsed_time{run_simulation(universe, dt, sim)};

  std::string marker = execute_serial ? "S" : "P";
  int num_threads = execute_serial ? 1 : omp_get_max_threads();

  std::cout 
    << marker << ";" 
    << universe.size << ";"
    << num_threads << ";"
    << elapsed_time << "\n";

  return 0;
}
