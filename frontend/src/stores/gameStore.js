import { defineStore } from 'pinia'
import { getConfig, getGame, getHistory, submitTurn } from '../api/client'

export const useGameStore = defineStore('game', {
  state: () => ({
    gameId: null,
    currentTurn: 0,
    status: 'running',
    gameLengthTurns: 120,
    snapshot: null,
    history: [],
    config: null,
  }),
  actions: {
    async load(gameId) {
      this.gameId = gameId
      this.snapshot = null
      this.history = []
      this.status = 'running'
      const [game, history, config] = await Promise.all([
        getGame(gameId),
        getHistory(gameId),
        getConfig(gameId),
      ])
      this.currentTurn = game.current_turn
      this.status = game.status
      this.gameLengthTurns = game.game_length_turns
      this.snapshot = game.snapshot
      this.history = history
      this.config = config
    },
    async advanceTurn(decision) {
      const game = await submitTurn(this.gameId, decision)
      this.currentTurn = game.current_turn
      this.status = game.status
      this.gameLengthTurns = game.game_length_turns
      this.snapshot = game.snapshot
      this.history.push(game.snapshot)
    },
  },
})
