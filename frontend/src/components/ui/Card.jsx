import clsx from 'clsx';

const Card = ({ children, className = '', title, subtitle, actions }) => {
  return (
    <div className={clsx(
      'bg-white rounded-xl shadow-lg overflow-hidden animate-fadeIn',
      className
    )}>
      {(title || subtitle || actions) && (
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
          <div>
            {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

export default Card;
