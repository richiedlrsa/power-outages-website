import { useEffect, useState } from 'react'
import './App.css'
import Loading from './loading'

type MaintenanceEvent = {
  time: string
  sectors: string[]
}

type Outage = {
  company: string
  week_number: string
  day: string
  province: string
  maintenance: MaintenanceEvent[]
}

function App() {
  const limit = 10
  const [outages, setOutages] = useState<Outage[]>([]);
  const [currPage, setCurrPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [searchResult, setSearchResult] = useState<Outage[]>([])
  const [provinces, setProvinces] = useState<Record<string, string[]>>({});
  const [formData, setFormData] = useState({company: '', province: '', sector: '', date: ''})
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    setIsLoading(true);
    
    const fetchData = async () => {
      try {
        const resp = await fetch('/outages/');
        const data = await resp.json();
        setOutages(data);
        setSearchResult(data)
      } catch (error) {
        console.error(`Error fetching data. ${error}`);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [])

  useEffect(() => {
    const provinceMap: Record<string, string[]> = {};
    
    if (!(outages.length > 0)) return;

    outages.forEach(outage => {
      const key: string = outage.province

      if (!(key in provinceMap)) {
        provinceMap[key] = []
      }

      outage.maintenance.forEach(maintenance => {
        const cleanSectors = maintenance.sectors.map(s => s.trim())
        provinceMap[key].push(...cleanSectors)
      })          
    })

    setProvinces(provinceMap)
  }, [outages])

  useEffect(() => {
    setTotalPages(Math.ceil(searchResult.length / limit))
  }, [searchResult])

  const handleChange = function(e: any) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value}))
  }

  const handleClick = function(e: any) {
    e.preventDefault();
    setCurrPage(1)

    if (!(outages.length > 0)) return;

    setIsLoading(true)
    
    const { company, province, sector, date } = formData

    let filteredOutages = outages.filter(outage => {
      const matchedProvince = !province || outage.province === province
      const matchedCompany = !company || outage.company === company
      const matchedDate = !date || outage.day === date

      return matchedProvince && matchedCompany && matchedDate
    })

    if (sector) {
      filteredOutages = filteredOutages.reduce((acc: Outage[], outage) => {
        const matchingMaintenance = outage.maintenance
          .filter(event => event.sectors.includes(sector))
          .map(event => ({
            'time': event.time,
            'sectors': [sector]
          }))

          if (matchingMaintenance.length > 0) {
            acc.push({
              ...outage,
              'maintenance': matchingMaintenance
            })
          };
          return acc;
      }, [])
    }

    setSearchResult(filteredOutages);
    setIsLoading(false);
  }

  const clearFilters = function(e: any) {
    e.preventDefault();
    
    setFormData({
      company: '',
      province: '',
      sector: '',
      date: '',
    })

    setSearchResult(outages)
  }

  return (
    <div>
      <header className='text-center mt-12 mb-12 py-10 bg-gradient-to-r from-[#e9f1ff] to-[#f9fafb] rounded-2xl shadow-sm'>
        <h1 className='text-[#0056b3] text-3xl sm:text-4xl font-extrabold mb-3 tracking-tight'>Apagones RD</h1>
        <p className='text-lg sm:text-xl text-[#6c757d] font-medium'>Encuentra mantenimientos programados en tu area</p>
      </header>

      <main className='min-h-screen flex flex-col items-center bg-[#f9fafb]'>
        <section className='bg-white border border-[#dee2e6] rounded-2xl p-10 mt-10 shadow-xl w-full'>
          <form method='get'>
            <div className='grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-y-6 gap-x-4 items-end'>

              {/* COMPANY */}
              <div className='flex flex-col'>
                <label htmlFor='company' className='text-[#374151] font-medium mb-1'>Compañía</label>
                <select 
                id='company' 
                name='company'
                value={formData.company}
                onChange={handleChange}
                disabled={isLoading}
                className='p-3 rounded-lg border border-[#e5e7eb] bg-white focus:outline-none focus:ring-2 focus:ring-[#2563eb] transition-all'
                >
                  <option value='' id='selected-company'>Selecciona una compañía</option>
                  <option value='Edeeste' id='edeeste'>Edeeste</option>
                  <option value='Edesur' id='edesur'>Edesur</option>
                  <option value='Edenorte' id='edenorte'>Edenorte</option>
                </select>
              </div>

              {/* PROVINCE */}
              <div className='flex flex-col'>
                <label htmlFor='province' className='text-[#374151] font-medium mb-1'>Provincia</label>
                <input 
                id='province' 
                name='province'
                list='province-list'
                value={formData.province}
                onChange={handleChange}
                disabled={isLoading}
                className='p-3 rounded-lg border border-[#e5e7eb] bg-white focus:outline-none focus:ring-2 focus:ring-[#2563eb] transition-all'
                />
                  <datalist id='province-list'>
                    {Object.keys(provinces).map(key => (
                      <option key={key} value={key} />
                    ))}
                  </datalist>
              </div>

              {/* SECTOR */}
              <div className='flex flex-col'>
                <label htmlFor='sector-input' className='text-[#374151] font-medium mb-1'>Sector</label>
                <input 
                type='text'
                id='sector' 
                name='sector'
                list='sector-list' 
                placeholder='e.g., Naco'
                value={formData.sector}
                onChange={handleChange}
                disabled={isLoading}
                className='p-3 rounded-lg border border-[#e5e7eb] bg-white focus:outline-none focus:ring-2 focus:ring-[#2563eb] transition-all'
                />
                <datalist id='sector-list'>
                  {formData.province && formData.province in provinces && (
                    provinces[formData.province].map(sector => (
                      <option key={sector} value={sector} />
                    ))
                  )}
                </datalist>
              </div>

              {/* DATE */}
              <div className='flex flex-col'>
                <label htmlFor='date' className='text-[#374151] font-medium mb-1'>Fecha</label>
                <input 
                type='date' 
                id='date' 
                name='date'
                value={formData.date}
                onChange={handleChange}
                disabled={isLoading}
                className='p-3 rounded-lg border border-[#e5e7eb] bg-white focus:outline-none focus:ring-2 focus:ring-[#2563eb] transition-all'
                />
              </div>

              {/* BUTTON */}
              <div className='col-span-full flex justify-end mt-6 gap-4'>
                <button
                type='submit'
                className='bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-semibold px-6 py-3 rounded-lg shadow-md transition-all active:scale-95'
                onClick={clearFilters}
                disabled={isLoading}
                >
                  Limpiar filtros
                </button>
              
                <button
                type='submit'
                className='bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-semibold px-6 py-3 rounded-lg shadow-md transition-all active:scale-95'
                onClick={handleClick}
                disabled={isLoading}
                >
                  Buscar
                </button>

              </div>

            </div>
          </form>
        </section>
        
        {/* TABLE SECTION */}
        {
          isLoading ?
          <Loading />
          :
          <section className='mt-10 bg-white border border-[#dee2e6] rounded-2xl shadow-xl w-full overflow-hidden'>
              <table className='table-auto w-full text-left border-collapse'>
                <thead className='bg-[#f8f9fa] text-[#374151] border-b border-[#dee2e6]'>
                  <tr>
                    <th className='border border-gray-300 px-6 py-3 font-semibold'>Compañía</th>
                    <th className='border border-gray-300 px-6 py-3 font-semibold'>provincia</th>
                    <th className='border border-gray-300 px-6 py-3 font-semibold'>Fecha</th>
                    <th className='border border-gray-300 px-6 py-3 font-semibold'>Hora</th>
                    <th className='border border-gray-300 px-6 py-3 font-semibold'>Sector</th>
                  </tr>
                </thead>

                <tbody id='data-table'>
                  {searchResult.length > 0 ? 
                  <>
                    {searchResult.slice((currPage - 1) * limit, currPage * limit).map(outage => (
                      <>
                        {outage.maintenance.map(maintenance => (
                          <tr className='border-b border-[#dee2e6]'>
                            <td className='border border-gray-200 px-6 py-3'>{outage.company}</td>
                            <td className='border border-gray-200 px-6 py-3 w-1/6'>{outage.province}</td>
                            <td className='border border-gray-200 px-6 py-3 w-1/8'>{outage.day}</td>
                            <td className='border border-gray-200 px-6 py-3 w-1/4'>{maintenance.time}</td>
                            <td className='border border-gray-200 px-6 py-3'>{maintenance.sectors.join(', ')}</td>
                          </tr>
                        ))}
                      </>
                    ))}
                  </>
                  :
                  <tr>
                    <td colSpan={5} className='text-center text-gray-500 py-6'>No hay datos</td>
                  </tr>
                }
                </tbody>
              </table>
            </section>
          }

        {/* PAGINATION */}
        <nav aria-label='pagination'>
          <ul className='inline-flex -space-x-px text-base h-10'>
            <li>
              <button
              className='flex items-center justify-center px-4 h-10 ms-0 leading-tight text-gray-500 bg-white border border-e-0 border-gray-300 rounded-s-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed'
              onClick={() => setCurrPage(currPage - 1)}
              disabled={currPage === 1 || isLoading}
              >
                Previous
              </button>
            </li>
            
            {Array.from({ length: totalPages + 1}).map((_, i) => (
              i > 0 && 
              <li>
                <button
                className='flex items-center justify-center px-4 h-10 ms-0 leading-tight text-gray-500 bg-white border border-e-0 border-gray-300 rounded-s-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed'
                onClick={() => setCurrPage(i)}
                disabled={currPage === i || searchResult.length === 0 || isLoading}
                >
                  {i}
                </button>
              </li>
            ))}

            <li>
              <button
              className='flex items-center justify-center px-4 h-10 ms-0 leading-tight text-gray-500 bg-white border border-e-0 border-gray-300 rounded-s-lg hover:bg-gray-100 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed'
              onClick={() => setCurrPage(currPage + 1)}
              disabled={currPage === totalPages || searchResult.length === 0 || isLoading}
              >
                Next
              </button>
            </li>

          </ul>
        </nav>
      </main>

      <footer className='text-center mt-40 bg-[#f1f3f5] text-[#374151] py-8 rounded-t-2xl border-[#dee2e6] hadow-inner'>
        <p className='text-sm sm:text-base'>
          Datos actualizados diariamente mediante nuestro{" "}
          <span className='text-[#2563eb] font-medium'>Power Outages Scraper</span>
          <br className='hidden sm:block' />
          Desarrollado por{" "}
          <span className='font-semibold text-[#2563eb]'>Richie de la Rosa</span>
        </p>
      </footer>
    </div>
  )
}
 

export default App
