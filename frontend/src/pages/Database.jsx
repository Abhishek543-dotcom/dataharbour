import { useState, useEffect } from 'react';
import { Database as DatabaseIcon, Table, Search, Play, Download, RefreshCw, ChevronRight } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Database = () => {
  const [databases, setDatabases] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableSchema, setTableSchema] = useState(null);
  const [tableData, setTableData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [queryMode, setQueryMode] = useState(false);
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/database/databases`);
      setDatabases(response.data.databases || []);
    } catch (error) {
      console.error('Error fetching databases:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTables = async (database) => {
    setLoading(true);
    setSelectedDatabase(database);
    setSelectedTable(null);
    setTableSchema(null);
    setTableData(null);
    try {
      const response = await axios.get(`${API_BASE}/database/databases/${database}/tables`);
      setTables(response.data.tables || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTableDetails = async (table) => {
    setLoading(true);
    setSelectedTable(table);
    try {
      const [schemaResponse, dataResponse] = await Promise.all([
        axios.get(`${API_BASE}/database/databases/${selectedDatabase}/tables/${table.schema}/${table.name}/schema`),
        axios.get(`${API_BASE}/database/databases/${selectedDatabase}/tables/${table.schema}/${table.name}/preview?limit=100`)
      ]);
      setTableSchema(schemaResponse.data);
      setTableData(dataResponse.data);
    } catch (error) {
      console.error('Error fetching table details:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/database/databases/${selectedDatabase}/query`, {
        query: query.trim(),
        limit: 1000
      });
      setQueryResult(response.data);
    } catch (error) {
      console.error('Error executing query:', error);
      setQueryResult({
        error: error.response?.data?.detail || 'Query execution failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = (data) => {
    if (!data || !data.rows || data.rows.length === 0) return;

    const headers = data.columns.join(',');
    const rows = data.rows.map(row =>
      data.columns.map(col => {
        const val = row[col];
        return typeof val === 'string' && val.includes(',') ? `"${val}"` : val;
      }).join(',')
    );

    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedTable?.name || 'query'}_export.csv`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Database Explorer</h1>
          <p className="text-gray-600 mt-1">Browse PostgreSQL databases, tables, and execute queries</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={!queryMode ? 'primary' : 'secondary'}
            onClick={() => setQueryMode(false)}
          >
            <Table className="w-4 h-4 mr-2" />
            Browse
          </Button>
          <Button
            variant={queryMode ? 'primary' : 'secondary'}
            onClick={() => setQueryMode(true)}
          >
            <Play className="w-4 h-4 mr-2" />
            Query
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Databases Sidebar */}
        <div className="col-span-3">
          <Card className="h-full">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Databases</h3>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={fetchDatabases}
                  disabled={loading}
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
            </div>
            <div className="p-2 space-y-1 max-h-[600px] overflow-y-auto">
              {databases.map((db) => (
                <button
                  key={db.name}
                  onClick={() => fetchTables(db.name)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedDatabase === db.name
                      ? 'bg-gradient-primary text-white'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <DatabaseIcon className="w-4 h-4" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{db.name}</div>
                      <div className="text-xs opacity-75">{db.size}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-9">
          {!queryMode ? (
            // Browse Mode
            <>
              {selectedDatabase && (
                <Card>
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900">
                      Tables in {selectedDatabase}
                    </h3>
                  </div>
                  <div className="p-4">
                    {tables.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Table className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No tables found in this database</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-3">
                        {tables.map((table) => (
                          <button
                            key={`${table.schema}.${table.name}`}
                            onClick={() => fetchTableDetails(table)}
                            className={`text-left p-4 rounded-lg border-2 transition-all ${
                              selectedTable?.name === table.name
                                ? 'border-primary-500 bg-primary-50'
                                : 'border-gray-200 hover:border-primary-300'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <Table className="w-5 h-5 text-primary-600 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-gray-900 truncate">
                                  {table.name}
                                </div>
                                <div className="text-sm text-gray-500 mt-1">
                                  {table.column_count} columns • {table.size}
                                </div>
                              </div>
                              <ChevronRight className="w-5 h-5 text-gray-400" />
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {tableSchema && tableData && (
                <Card className="mt-6">
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {tableSchema.schema}.{tableSchema.table}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {tableSchema.row_count} rows total • Showing {tableData.rows.length} rows
                        </p>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => exportToCSV(tableData)}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export CSV
                      </Button>
                    </div>
                  </div>

                  {/* Schema Info */}
                  <div className="p-4 bg-gray-50 border-b border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Schema</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {tableSchema.columns.map((col) => (
                        <div
                          key={col.name}
                          className="flex items-center gap-2 text-sm"
                        >
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            tableSchema.primary_keys.includes(col.name)
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-200 text-gray-700'
                          }`}>
                            {col.type}
                          </span>
                          <span className="font-medium">{col.name}</span>
                          {tableSchema.primary_keys.includes(col.name) && (
                            <span className="text-xs text-yellow-600">(PK)</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Table Data */}
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          {tableData.columns.map((col) => (
                            <th
                              key={col}
                              className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {tableData.rows.map((row, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            {tableData.columns.map((col) => (
                              <td
                                key={col}
                                className="px-4 py-3 text-sm text-gray-900"
                              >
                                {row[col] === null ? (
                                  <span className="text-gray-400 italic">null</span>
                                ) : (
                                  String(row[col])
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          ) : (
            // Query Mode
            <Card>
              <div className="p-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">SQL Query Editor</h3>
                {selectedDatabase && (
                  <p className="text-sm text-gray-600 mt-1">
                    Connected to: {selectedDatabase}
                  </p>
                )}
              </div>
              <div className="p-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your SELECT query here..."
                  className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={!selectedDatabase}
                />
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    Only SELECT queries are allowed • Max 1000 rows
                  </p>
                  <Button
                    variant="primary"
                    onClick={executeQuery}
                    disabled={!selectedDatabase || !query.trim() || loading}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Execute Query
                  </Button>
                </div>
              </div>

              {queryResult && (
                <div className="border-t border-gray-200">
                  {queryResult.error ? (
                    <div className="p-4 bg-red-50 text-red-700">
                      <p className="font-semibold">Error:</p>
                      <p className="mt-1">{queryResult.error}</p>
                    </div>
                  ) : (
                    <>
                      <div className="p-4 bg-gray-50 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-gray-600">
                            {queryResult.row_count} rows returned
                          </p>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => exportToCSV(queryResult)}
                          >
                            <Download className="w-4 h-4 mr-2" />
                            Export
                          </Button>
                        </div>
                      </div>
                      <div className="overflow-x-auto max-h-[500px]">
                        <table className="w-full">
                          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                            <tr>
                              {queryResult.columns.map((col) => (
                                <th
                                  key={col}
                                  className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                                >
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {queryResult.rows.map((row, idx) => (
                              <tr key={idx} className="hover:bg-gray-50">
                                {queryResult.columns.map((col) => (
                                  <td
                                    key={col}
                                    className="px-4 py-3 text-sm text-gray-900"
                                  >
                                    {row[col] === null ? (
                                      <span className="text-gray-400 italic">null</span>
                                    ) : (
                                      String(row[col])
                                    )}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Database;
