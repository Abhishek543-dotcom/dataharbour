import { useState, useEffect } from 'react';
import { HardDrive, Folder, File, Download, Trash2, RefreshCw, Upload, FolderPlus } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Storage = () => {
  const [buckets, setBuckets] = useState([]);
  const [selectedBucket, setSelectedBucket] = useState(null);
  const [objects, setObjects] = useState([]);
  const [currentPath, setCurrentPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [bucketStats, setBucketStats] = useState(null);
  const [showCreateBucket, setShowCreateBucket] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [newBucketName, setNewBucketName] = useState('');
  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    fetchBuckets();
  }, []);

  const fetchBuckets = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/storage/buckets`);
      setBuckets(response.data.buckets || []);
    } catch (error) {
      console.error('Error fetching buckets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBucketStats = async (bucketName) => {
    try {
      const response = await axios.get(`${API_BASE}/storage/buckets/${bucketName}/stats`);
      setBucketStats(response.data);
    } catch (error) {
      console.error('Error fetching bucket stats:', error);
    }
  };

  const fetchObjects = async (bucketName, prefix = '') => {
    setLoading(true);
    setSelectedBucket(bucketName);
    setCurrentPath(prefix);
    try {
      const response = await axios.get(
        `${API_BASE}/storage/buckets/${bucketName}/objects?prefix=${prefix}&recursive=false`
      );
      setObjects(response.data.objects || []);
      fetchBucketStats(bucketName);
    } catch (error) {
      console.error('Error fetching objects:', error);
    } finally {
      setLoading(false);
    }
  };

  const createBucket = async () => {
    if (!newBucketName.trim()) return;

    try {
      await axios.post(`${API_BASE}/storage/buckets`, {
        bucket_name: newBucketName.trim()
      });
      setNewBucketName('');
      setShowCreateBucket(false);
      fetchBuckets();
    } catch (error) {
      console.error('Error creating bucket:', error);
    }
  };

  const deleteBucket = async (bucketName) => {
    if (!confirm(`Are you sure you want to delete bucket "${bucketName}"?`)) return;

    try {
      await axios.delete(`${API_BASE}/storage/buckets/${bucketName}`);
      setSelectedBucket(null);
      setObjects([]);
      fetchBuckets();
    } catch (error) {
      console.error('Error deleting bucket:', error);
      alert('Failed to delete bucket. Make sure it is empty.');
    }
  };

  const uploadFileToStorage = async () => {
    if (!uploadFile || !selectedBucket) return;

    const formData = new FormData();
    formData.append('file', uploadFile);

    const objectPath = currentPath ? `${currentPath}/${uploadFile.name}` : uploadFile.name;

    try {
      await axios.post(
        `${API_BASE}/storage/buckets/${selectedBucket}/objects/${objectPath}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      setUploadFile(null);
      setShowUpload(false);
      fetchObjects(selectedBucket, currentPath);
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const downloadObject = async (objectName) => {
    try {
      const response = await axios.get(
        `${API_BASE}/storage/buckets/${selectedBucket}/objects/${objectName}/download`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', objectName.split('/').pop());
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading object:', error);
    }
  };

  const deleteObject = async (objectName) => {
    if (!confirm(`Are you sure you want to delete "${objectName}"?`)) return;

    try {
      await axios.delete(`${API_BASE}/storage/buckets/${selectedBucket}/objects/${objectName}`);
      fetchObjects(selectedBucket, currentPath);
    } catch (error) {
      console.error('Error deleting object:', error);
    }
  };

  const navigateToFolder = (folderName) => {
    fetchObjects(selectedBucket, folderName.replace(/\/$/, ''));
  };

  const navigateUp = () => {
    const pathParts = currentPath.split('/');
    pathParts.pop();
    const newPath = pathParts.join('/');
    fetchObjects(selectedBucket, newPath);
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Storage Browser</h1>
          <p className="text-gray-600 mt-1">Browse and manage MinIO object storage</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={fetchBuckets}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="primary" onClick={() => setShowCreateBucket(true)}>
            <FolderPlus className="w-4 h-4 mr-2" />
            New Bucket
          </Button>
        </div>
      </div>

      {/* Bucket Stats */}
      {bucketStats && (
        <div className="grid grid-cols-3 gap-6">
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary-100 rounded-lg">
                  <HardDrive className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Bucket</p>
                  <p className="text-xl font-bold text-gray-900">{bucketStats.bucket_name}</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <File className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Objects</p>
                  <p className="text-xl font-bold text-gray-900">{bucketStats.total_objects}</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-green-100 rounded-lg">
                  <HardDrive className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Size</p>
                  <p className="text-xl font-bold text-gray-900">{bucketStats.total_size_human}</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Buckets Sidebar */}
        <div className="col-span-3">
          <Card className="h-full">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Buckets</h3>
            </div>
            <div className="p-2 space-y-1 max-h-[600px] overflow-y-auto">
              {buckets.map((bucket) => (
                <div
                  key={bucket.name}
                  className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                    selectedBucket === bucket.name
                      ? 'bg-gradient-primary text-white'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <button
                    onClick={() => fetchObjects(bucket.name)}
                    className="flex items-center gap-2 flex-1 text-left"
                  >
                    <Folder className="w-4 h-4" />
                    <span className="font-medium truncate">{bucket.name}</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteBucket(bucket.name);
                    }}
                    className="p-1 hover:bg-red-500/20 rounded transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Objects Browser */}
        <div className="col-span-9">
          {selectedBucket ? (
            <Card>
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{selectedBucket}</h3>
                    {currentPath && (
                      <>
                        <span className="text-gray-400">/</span>
                        <span className="text-gray-600">{currentPath}</span>
                      </>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {currentPath && (
                      <Button variant="secondary" size="sm" onClick={navigateUp}>
                        ← Back
                      </Button>
                    )}
                    <Button variant="primary" size="sm" onClick={() => setShowUpload(true)}>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload
                    </Button>
                  </div>
                </div>
              </div>
              <div className="p-4">
                {objects.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Folder className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No objects in this location</p>
                  </div>
                ) : (
                  <div className="grid gap-2">
                    {objects.map((obj) => (
                      <div
                        key={obj.name}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          {obj.is_dir ? (
                            <Folder className="w-5 h-5 text-yellow-500 flex-shrink-0" />
                          ) : (
                            <File className="w-5 h-5 text-blue-500 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">
                              {obj.name.split('/').pop() || obj.name}
                            </p>
                            {!obj.is_dir && (
                              <p className="text-sm text-gray-500">
                                {formatSize(obj.size)} • {new Date(obj.last_modified).toLocaleString()}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {obj.is_dir ? (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => navigateToFolder(obj.name)}
                            >
                              Open
                            </Button>
                          ) : (
                            <>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => downloadObject(obj.name)}
                              >
                                <Download className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => deleteObject(obj.name)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card>
              <div className="p-12 text-center text-gray-500">
                <HardDrive className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Select a bucket to browse its contents</p>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Create Bucket Modal */}
      <Modal
        isOpen={showCreateBucket}
        onClose={() => {
          setShowCreateBucket(false);
          setNewBucketName('');
        }}
        title="Create New Bucket"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bucket Name
            </label>
            <input
              type="text"
              value={newBucketName}
              onChange={(e) => setNewBucketName(e.target.value)}
              placeholder="my-bucket-name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Lowercase letters, numbers, and hyphens only
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowCreateBucket(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={createBucket} disabled={!newBucketName.trim()}>
              Create Bucket
            </Button>
          </div>
        </div>
      </Modal>

      {/* Upload Modal */}
      <Modal
        isOpen={showUpload}
        onClose={() => {
          setShowUpload(false);
          setUploadFile(null);
        }}
        title="Upload File"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File
            </label>
            <input
              type="file"
              onChange={(e) => setUploadFile(e.target.files[0])}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            {uploadFile && (
              <p className="text-sm text-gray-600 mt-2">
                Selected: {uploadFile.name} ({formatSize(uploadFile.size)})
              </p>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowUpload(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={uploadFileToStorage} disabled={!uploadFile}>
              Upload
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Storage;
