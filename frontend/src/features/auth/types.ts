export type TokenOut = {
  access_token: string
  token_type: string
}

export type UserOut = {
  id: number
  email: string
  name: string
}

export type LoginResponse = {
  token: TokenOut
  user: UserOut
}

export type LoginBody = {
  email: string
  password: string
}

export type RegisterBody = {
  name: string
  email: string
  password: string
  confirm_password: string
}

export type RegisterResponse = LoginResponse
