import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api/users'
import PageContainer from '@/components/layout/PageContainer'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormModal } from '@/components/ui/FormModal'
import { toast } from '@/stores/toastStore'
import { KeyRound, Plus, Pencil, Trash2, Users, Check, X, Loader2 } from 'lucide-react'
import type { AppProfile, User } from '@/types/auth.types'
import { normalizeAppProfile } from '@/lib/appProfile'

const selectClassName =
  'rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500'

export default function UsersPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [passwordUser, setPasswordUser] = useState<User | null>(null)
  
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isSuperuser, setIsSuperuser] = useState(false)
  const [appProfile, setAppProfile] = useState<AppProfile>('full')
  
  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  })

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      toast.success('Usuário criado com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao criar usuário. Verifique os dados.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof usersApi.update>[1] }) =>
      usersApi.update(id, data),
    onSuccess: () => {
      toast.success('Usuário atualizado com sucesso!')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      resetForm()
    },
    onError: () => {
      toast.error('Erro ao atualizar usuário.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      toast.success('Usuário excluído com sucesso!')
      setDeleteConfirm(null)
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: () => {
      toast.error('Erro ao excluir usuário.')
      setDeleteConfirm(null)
    },
  })

  const changePasswordMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { new_password: string } }) =>
      usersApi.changePassword(id, data),
    onSuccess: () => {
      toast.success('Senha alterada com sucesso!')
      setPasswordUser(null)
      setNewPassword('')
      setConfirmPassword('')
    },
    onError: () => {
      toast.error('Erro ao alterar a senha do usuário.')
    },
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      usersApi.toggleActive(id, is_active),
    onSuccess: (_, variables) => {
      toast.success(variables.is_active ? 'Usuário ativado!' : 'Usuário desativado!')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: () => {
      toast.error('Erro ao alterar status do usuário.')
    },
  })

  const resetForm = () => {
    setEmail('')
    setFullName('')
    setPassword('')
    setIsSuperuser(false)
    setAppProfile('full')
    setShowForm(false)
    setEditing(null)
  }

  const handleEdit = (user: User) => {
    setEditing(user)
    setEmail(user.email)
    setFullName(user.full_name)
    setIsSuperuser(user.is_superuser)
    setAppProfile(normalizeAppProfile(user.app_profile))
    setPassword('')
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const profile = appProfile
    const superuserFlag = profile === 'checklist' ? true : isSuperuser
    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        data: { full_name: fullName, is_superuser: superuserFlag, app_profile: profile },
      })
    } else {
      createMutation.mutate({
        email,
        full_name: fullName,
        password,
        is_superuser: superuserFlag,
        app_profile: profile,
      })
    }
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!passwordUser) {
      return
    }

    if (newPassword.length < 8) {
      toast.error('A nova senha deve ter pelo menos 8 caracteres.')
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error('A confirmação da senha não confere.')
      return
    }

    changePasswordMutation.mutate({
      id: passwordUser.id,
      data: { new_password: newPassword },
    })
  }

  return (
    <PageContainer
      title="Usuários"
      subtitle="Gerenciar usuários do sistema"
      action={
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4 mr-1" />
          Novo Usuário
        </Button>
      }
    >
      <FormModal
        open={showForm}
        title={editing ? 'Editar usuário' : 'Novo usuário'}
        description={editing ? undefined : 'Preencha os dados do usuário antes de salvar.'}
        onClose={resetForm}
      >
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Nome Completo"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder={editing ? undefined : 'João Silva'}
            required
          />
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={editing ? undefined : 'joao@email.com'}
            disabled={!!editing}
            required
          />
          {!editing && (
            <Input
              label="Senha"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo 8 caracteres"
              required={!editing}
            />
          )}
          <div className="flex flex-col gap-1 sm:col-span-2">
            <label className="text-sm font-medium text-slate-700">Perfil no app</label>
            <select
              className={selectClassName}
              value={appProfile}
              onChange={(e) => {
                const value = e.target.value as AppProfile
                setAppProfile(value)
                if (value === 'checklist') setIsSuperuser(true)
              }}
            >
              <option value="full">Completo (admin / gestão)</option>
              <option value="checklist">Checklist (só conferências)</option>
            </select>
            {!editing ? (
              <p className="text-xs text-slate-500">
                Checklist: ao entrar, vê apenas Entrada/Saída. Completo: sistema igual ao de vocês.
              </p>
            ) : null}
          </div>
          {appProfile === 'full' ? (
            <div className="flex items-center gap-2 sm:col-span-2">
              <input
                type="checkbox"
                id="isSuperuser"
                checked={isSuperuser}
                onChange={(e) => setIsSuperuser(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary-600"
              />
              <label htmlFor="isSuperuser" className="text-sm text-slate-700">
                Administrador (acesso a usuários e todos os dados)
              </label>
            </div>
          ) : null}
          <div className="sm:col-span-2 flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {createMutation.isPending || updateMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : null}
              {editing ? 'Salvar alterações' : 'Criar usuário'}
            </Button>
          </div>
        </form>
      </FormModal>

      <FormModal
        open={!!passwordUser}
        title="Alterar senha"
        description={passwordUser ? `Defina uma nova senha para ${passwordUser.full_name}.` : undefined}
        onClose={() => {
          setPasswordUser(null)
          setNewPassword('')
          setConfirmPassword('')
        }}
      >
        <form onSubmit={handlePasswordSubmit} className="grid gap-4">
          <Input
            label="Nova senha"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Mínimo 8 caracteres"
            required
          />
          <Input
            label="Confirmar nova senha"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Repita a nova senha"
            required
          />
          <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setPasswordUser(null)
                setNewPassword('')
                setConfirmPassword('')
              }}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={changePasswordMutation.isPending}>
              {changePasswordMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : null}
              Salvar nova senha
            </Button>
          </div>
        </form>
      </FormModal>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          Carregando...
        </div>
      )}

      {!isLoading && users.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <Users className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="font-medium">Nenhum usuário cadastrado</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && users.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {users.map((user) => (
            <Card key={user.id} className="group">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-slate-900 truncate">{user.full_name}</h3>
                    <p className="text-sm text-slate-500 truncate">{user.email}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      <Badge variant={user.is_active ? 'success' : 'default'}>{user.is_active ? 'Ativo' : 'Inativo'}</Badge>
                      {normalizeAppProfile(user.app_profile) === 'checklist' ? (
                        <Badge variant="warning">Checklist</Badge>
                      ) : user.is_superuser ? (
                        <Badge variant="info">Admin</Badge>
                      ) : (
                        <Badge variant="default">Completo</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleEdit(user)}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setPasswordUser(user)}>
                    <KeyRound className="h-3 w-3 text-slate-600" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => toggleActiveMutation.mutate({ id: user.id, is_active: !user.is_active })} disabled={toggleActiveMutation.isPending}>
                    {user.is_active ? <X className="h-3 w-3 text-yellow-500" /> : <Check className="h-3 w-3 text-green-500" />}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleteConfirm(user.id)}>
                    <Trash2 className="h-3 w-3 text-red-500" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteConfirm}
        title="Excluir Usuário"
        message="Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </PageContainer>
  )
}