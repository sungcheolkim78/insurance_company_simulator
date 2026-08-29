import { defineStore } from 'pinia'
import { getConfig, getGame, getHistory, submitTurn } from '../api/client'

export const useGameStore = defineStore('game', {
  state: () => ({
    gameId: null,
    currentTurn: 0,
    status: 'running',
    snapshot: null,
    history: [],
    config: null,
  }),
  actions: {
    async load(gameId) {
      this.gameId = gameId
      const [game, history, config] = await Promise.all([
        getGame(gameId),
        getHistory(gameId),
        getConfig(gameId),
      ])
      this.currentTurn = game.current_turn
      this.status = game.status
      this.snapshot = game.snapshot
      this.history = history
      this.config = config
    },
    async advanceTurn(decision) {
      const game = await submitTurn(this.gameId, decision)
      this.currentTurn = game.current_turn
      this.status = game.status
      this.snapshot = game.snapshot
      this.history.push(game.snapshot)
    },
  },
})
