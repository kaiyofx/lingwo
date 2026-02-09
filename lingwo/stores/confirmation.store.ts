// ~/stores/confirmation.ts

interface IConfirmationStore {
  username: string
  email: string
  password: string
}

const defaultValue: { confirm: IConfirmationStore} = {
  confirm: {
    username: '',
    email: '',
    password: '',
  },
}

export const useConfirmationStore = defineStore('confirmation', {
  state: () => defaultValue,
  actions: {
    clear() {
      this.$patch(defaultValue)
    },
    set(input: IConfirmationStore) {
      this.$patch({confirm: input})
    }
  }
})
