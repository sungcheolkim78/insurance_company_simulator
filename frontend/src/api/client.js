import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

export async function createGame(initialCapital, rngSeed) {
  const response = await apiClient.post('/games', {
    initial_capital: initialCapital,
    rng_seed: rngSeed ?? null,
  })
  return response.data
}

export async function getGame(gameId) {
  const response = await apiClient.get(`/games/${gameId}`)
  return response.data
}

export async function getHistory(gameId) {
  const response = await apiClient.get(`/games/${gameId}/history`)
  return response.data
}

export async function getConfig(gameId) {
  const response = await apiClient.get(`/games/${gameId}/config`)
  return response.data
}

export async function submitTurn(gameId, decision) {
  const response = await apiClient.post(`/games/${gameId}/turn`, decision)
  return response.data
}

export async function deleteGame(gameId) {
  await apiClient.delete(`/games/${gameId}`)
}
