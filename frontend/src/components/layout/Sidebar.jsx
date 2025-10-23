import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  Server,
  Activity,
  Settings,
} from 'lucide-react';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Notebooks', href: '/notebooks', icon: FileText },
  { name: 'Jobs', href: '/jobs', icon: Briefcase },
  { name: 'Clusters', href: '/clusters', icon: Server },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const Sidebar = () => {
  return (
    <div className="w-64 bg-white bg-opacity-95 backdrop-blur-lg border-r border-gray-200 shadow-xl flex flex-col">
      {/* Logo */}
      <div className="p-6">
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-primary rounded-xl text-white">
          <Server className="w-6 h-6" />
          <span className="font-bold text-lg">DataHarbour</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-gradient-primary text-white shadow-md transform translate-x-1'
                  : 'text-gray-700 hover:bg-gray-100 hover:translate-x-1'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={clsx('w-5 h-5', isActive ? 'text-white' : 'text-gray-500')} />
                {item.name}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          <p>DataHarbour v1.0.0</p>
          <p className="mt-1">© 2025 All rights reserved</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
