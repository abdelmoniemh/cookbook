import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { BrowsePage } from './pages/Browse'
import { CookPage } from './pages/Cook'
import { EditorPage } from './pages/Editor'
import { ImportPage } from './pages/Import'
import { NotFound } from './pages/NotFound'
import { PlanPage } from './pages/Plan'
import { RecipePage } from './pages/Recipe'
import { ShoppingPage } from './pages/Shopping'
import { ScrollReset } from './components/ScrollReset'

export function App() {
  return (
    <>
      <ScrollReset />
      <Routes>
        <Route path="/r/:slug/cook" element={<CookPage />} />
        <Route element={<AppShell />}>
          <Route index element={<BrowsePage />} />
          <Route path="/r/:slug" element={<RecipePage />} />
          <Route path="/r/:slug/edit" element={<EditorPage key="edit" />} />
          <Route path="/new" element={<EditorPage key="new" />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/plan" element={<PlanPage />} />
          <Route path="/shopping" element={<ShoppingPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  )
}
