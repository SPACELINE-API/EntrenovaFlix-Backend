import { Injectable } from '@nestjs/common';
import { supabase } from '../supabase/supabase.client';

@Injectable()
export class AuthService {
  async login(email: string, password: string) {
    return await supabase.auth.signInWithPassword({
      email,
      password,
    });
  }

  async validarToken(token: string) {
    const { data, error } = await supabase.auth.getUser(token);
    if (error || !data.user) {
      throw new Error('Token inválido');
    }
    return data.user;
  }
}