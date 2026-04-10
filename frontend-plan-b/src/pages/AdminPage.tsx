import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { api } from "../lib/api";
import type { AppSettings, PlayerRecord, StaffRole, StaffUser, TableRecord } from "../types/models";

const roleLabels: Record<string, string> = {
  super_admin: "супер-админ",
  admin: "админ",
  host: "ведущий",
};

export function AdminPage() {
  const { token, user } = useAuth();
  const [tables, setTables] = useState<TableRecord[]>([]);
  const [players, setPlayers] = useState<PlayerRecord[]>([]);
  const [staff, setStaff] = useState<StaffUser[]>([]);
  const [settings, setSettings] = useState<AppSettings>({ default_price_per_game: 2500 });
  const [tableName, setTableName] = useState("");
  const [staffForm, setStaffForm] = useState({ login: "", password: "", name: "", role: "host" as StaffRole });

  async function load() {
    if (!token) return;
    const [tablesResponse, playersResponse] = await Promise.all([api.listTables(token), api.listPlayers(token)]);
    setTables(tablesResponse);
    setPlayers(playersResponse.items);
    try {
      setSettings(await api.getSettings(token));
    } catch {
      setSettings({ default_price_per_game: 2500 });
    }
    if (user?.role === "super_admin") {
      setStaff(await api.listStaff(token));
    }
  }

  useEffect(() => {
    void load();
  }, [token, user?.role]);

  async function handleCreateTable(event: FormEvent) {
    event.preventDefault();
    if (!token || !tableName.trim()) return;
    await api.createTable(token, tableName.trim());
    setTableName("");
    await load();
  }

  async function handleSaveSettings(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    await api.updateSettings(token, settings);
    await load();
  }

  async function handleCreateStaff(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    await api.createStaff(token, staffForm);
    setStaffForm({ login: "", password: "", name: "", role: "host" });
    await load();
  }

  return (
    <div className="page-stack">
      <section className="section-card">
        <div className="section-heading">
          <h2>Настройки</h2>
          <small>Глобальные настройки приложения.</small>
        </div>
        <form className="inline-form" onSubmit={handleSaveSettings}>
          <input
            type="number"
            value={settings.default_price_per_game}
            onChange={(event) => setSettings((current) => ({ ...current, default_price_per_game: Number(event.target.value) }))}
            placeholder="Цена по умолчанию"
          />
          <button type="submit">Сохранить цену по умолчанию</button>
        </form>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>Столы</h2>
          <small>Справочник столов для игр.</small>
        </div>
        <form className="inline-form" onSubmit={handleCreateTable}>
          <input value={tableName} onChange={(event) => setTableName(event.target.value)} placeholder="Новый стол" />
          <button type="submit">Добавить</button>
        </form>
        <div className="plain-list">
          {tables.map((table) => (
            <div key={table.id} className="plain-row">
              <span>{table.name}</span>
              <button onClick={() => token && api.deleteTable(token, table.id).then(load)}>{`Удалить`}</button>
            </div>
          ))}
        </div>
      </section>

      <section className="section-card">
        <div className="section-heading">
          <h2>База игроков</h2>
          <small>Глобальные профили игроков.</small>
        </div>
        <div className="plain-list">
          {players.map((player) => (
            <div key={player.id} className="plain-row">
              <span>
                {player.nick} <small>{player.name}</small>
              </span>
            </div>
          ))}
        </div>
      </section>

      {user?.role === "super_admin" ? (
        <section className="section-card">
          <div className="section-heading">
            <h2>Аккаунты сотрудников</h2>
            <small>Только для супер-админа.</small>
          </div>
          <form className="form-grid" onSubmit={handleCreateStaff}>
            <input placeholder="Логин" value={staffForm.login} onChange={(event) => setStaffForm((current) => ({ ...current, login: event.target.value }))} />
            <input placeholder="Имя" value={staffForm.name} onChange={(event) => setStaffForm((current) => ({ ...current, name: event.target.value }))} />
            <input
              placeholder="Пароль"
              type="password"
              value={staffForm.password}
              onChange={(event) => setStaffForm((current) => ({ ...current, password: event.target.value }))}
            />
            <select value={staffForm.role} onChange={(event) => setStaffForm((current) => ({ ...current, role: event.target.value as StaffRole }))}>
              <option value="host">Ведущий</option>
              <option value="admin">Админ</option>
              <option value="super_admin">Супер-админ</option>
            </select>
            <button className="primary-button" type="submit">
              Создать аккаунт
            </button>
          </form>
          <div className="plain-list">
            {staff.map((item) => (
              <div key={item.id} className="plain-row">
                <span>
                  {item.name} <small>{roleLabels[item.role] ?? item.role}</small>
                </span>
                <button onClick={() => token && api.deleteStaff(token, item.id).then(load)}>Удалить</button>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
