import { Controller, Post, Body, UnauthorizedException } from '@nestjs/common';
import { AuthService } from './auth.service';

@Controller('autenticacao')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  async login(
    @Body() body: { email: string; password: string },
  ): Promise<any> {
    const { email, password } = body;

    const { data: session, error } = await this.authService.login(email, password);

    if (error || !session.session) {
      throw new UnauthorizedException('Credenciais inválidas');
    }

    return {
      access_token: session.session.access_token,
      user: session.session.user,
    };
  }
}