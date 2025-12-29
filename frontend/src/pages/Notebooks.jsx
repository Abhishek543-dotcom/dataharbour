import { useState, useEffect } from 'react';
import { FileText, Plus, Download, Upload, ArrowLeft } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import NotebookList from '../components/notebook/NotebookList';
import NotebookCell from '../components/notebook/NotebookCell';
import { notebooksAPI } from '../services/api';

const Notebooks = () => {
  const [notebooks, setNotebooks] = useState([]);
  const [selectedNotebook, setSelectedNotebook] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(null);
  const [newNotebook, setNewNotebook] = useState({
    name: '',
    description: ''
  });

  // Load notebooks
  useEffect(() => {
    loadNotebooks();
  }, []);

  const loadNotebooks = async () => {
    try {
      const response = await notebooksAPI.getAll();
      setNotebooks(response.data);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    }
  };

  const loadNotebook = async (notebook) => {
    try {
      const response = await notebooksAPI.getById(notebook.id);
      setSelectedNotebook(response.data);
    } catch (error) {
      console.error('Failed to load notebook:', error);
    }
  };

  const handleCreateNotebook = async () => {
    if (!newNotebook.name.trim()) {
      return;
    }

    setLoading(true);
    try {
      const response = await notebooksAPI.create(newNotebook);
      setNotebooks([...notebooks, response.data]);
      setNewNotebook({ name: '', description: '' });
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create notebook:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNotebook = async (id) => {
    if (!confirm('Are you sure you want to delete this notebook?')) {
      return;
    }

    try {
      await notebooksAPI.delete(id);
      setNotebooks(notebooks.filter(n => n.id !== id));
      if (selectedNotebook?.id === id) {
        setSelectedNotebook(null);
      }
    } catch (error) {
      console.error('Failed to delete notebook:', error);
    }
  };

  const handleAddCell = async () => {
    if (!selectedNotebook) return;

    const newCell = {
      id: `cell-${Date.now()}`,
      cell_type: 'code',
      source: '',
      outputs: [],
      execution_count: null
    };

    const updatedNotebook = {
      ...selectedNotebook,
      cells: [...selectedNotebook.cells, newCell]
    };

    try {
      await notebooksAPI.update(selectedNotebook.id, {
        cells: updatedNotebook.cells
      });
      setSelectedNotebook(updatedNotebook);
    } catch (error) {
      console.error('Failed to add cell:', error);
    }
  };

  const handleDeleteCell = async (cellId) => {
    if (!selectedNotebook) return;

    const updatedCells = selectedNotebook.cells.filter(c => c.id !== cellId);
    const updatedNotebook = {
      ...selectedNotebook,
      cells: updatedCells
    };

    try {
      await notebooksAPI.update(selectedNotebook.id, {
        cells: updatedCells
      });
      setSelectedNotebook(updatedNotebook);
    } catch (error) {
      console.error('Failed to delete cell:', error);
    }
  };

  const handleMoveCell = async (cellId, direction) => {
    if (!selectedNotebook) return;

    const cells = [...selectedNotebook.cells];
    const index = cells.findIndex(c => c.id === cellId);

    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === cells.length - 1)
    ) {
      return;
    }

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    [cells[index], cells[newIndex]] = [cells[newIndex], cells[index]];

    const updatedNotebook = {
      ...selectedNotebook,
      cells
    };

    try {
      await notebooksAPI.update(selectedNotebook.id, { cells });
      setSelectedNotebook(updatedNotebook);
    } catch (error) {
      console.error('Failed to move cell:', error);
    }
  };

  const handleExecuteCell = async (cellId, code) => {
    if (!selectedNotebook) return;

    setExecuting(cellId);

    try {
      const response = await notebooksAPI.executeCell(
        selectedNotebook.id,
        cellId,
        code
      );

      // Update cell with output
      const updatedCells = selectedNotebook.cells.map(cell => {
        if (cell.id === cellId) {
          return {
            ...cell,
            source: code,
            outputs: response.data.output ? [{
              output_type: response.data.status === 'error' ? 'error' : 'stream',
              text: response.data.output,
              ename: response.data.status === 'error' ? 'Error' : undefined,
              evalue: response.data.status === 'error' ? 'Execution failed' : undefined,
              traceback: response.data.status === 'error' ? [response.data.output] : undefined
            }] : [],
            execution_count: cell.execution_count ? cell.execution_count + 1 : 1
          };
        }
        return cell;
      });

      setSelectedNotebook({
        ...selectedNotebook,
        cells: updatedCells
      });
    } catch (error) {
      console.error('Failed to execute cell:', error);
    } finally {
      setExecuting(null);
    }
  };

  const handleExport = async () => {
    if (!selectedNotebook) return;

    try {
      const response = await notebooksAPI.export(selectedNotebook.id);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedNotebook.name}.ipynb`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export notebook:', error);
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      await notebooksAPI.import(file);
      await loadNotebooks();
    } catch (error) {
      console.error('Failed to import notebook:', error);
    }
  };

  const handleBack = () => {
    setSelectedNotebook(null);
  };

  return (
    <div className="space-y-6">
      {/* List View */}
      {!selectedNotebook && (
        <Card
          title="Notebooks"
          subtitle="Manage your Jupyter-style notebooks"
          action={
            <div className="flex gap-2">
              <label>
                <input
                  type="file"
                  accept=".ipynb"
                  onChange={handleImport}
                  className="hidden"
                />
                <Button variant="secondary">
                  <Upload className="w-4 h-4 mr-2" />
                  Import
                </Button>
              </label>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                New Notebook
              </Button>
            </div>
          }
        >
          <NotebookList
            notebooks={notebooks}
            onSelect={loadNotebook}
            onDelete={handleDeleteNotebook}
          />
        </Card>
      )}

      {/* Editor View */}
      {selectedNotebook && (
        <Card
          title={
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBack}
              >
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <FileText className="w-5 h-5 text-purple-500" />
              <span>{selectedNotebook.name}</span>
            </div>
          }
          subtitle={selectedNotebook.description}
          action={
            <div className="flex gap-2">
              <Button variant="secondary" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button onClick={handleAddCell}>
                <Plus className="w-4 h-4 mr-2" />
                Add Cell
              </Button>
            </div>
          }
        >
          {selectedNotebook.cells.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No cells yet. Add your first cell to get started.</p>
              <Button onClick={handleAddCell}>
                <Plus className="w-4 h-4 mr-2" />
                Add Cell
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {selectedNotebook.cells.map((cell, index) => (
                <NotebookCell
                  key={cell.id}
                  cell={cell}
                  onExecute={handleExecuteCell}
                  onDelete={handleDeleteCell}
                  onMove={handleMoveCell}
                  isFirst={index === 0}
                  isLast={index === selectedNotebook.cells.length - 1}
                  executing={executing === cell.id}
                />
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Create Notebook Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Notebook"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notebook Name
            </label>
            <input
              type="text"
              value={newNotebook.name}
              onChange={(e) => setNewNotebook({ ...newNotebook, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="My Notebook"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <textarea
              value={newNotebook.description}
              onChange={(e) => setNewNotebook({ ...newNotebook, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows="3"
              placeholder="A brief description of this notebook"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateNotebook}
              disabled={loading || !newNotebook.name.trim()}
            >
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Notebooks;
