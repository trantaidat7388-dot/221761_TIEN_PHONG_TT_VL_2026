import { dungXacThuc } from '../../../context/AuthContext'
import { TrangChuyenDoi } from '../../chuyen_doi'

const TabChuyenDoiAdmin = () => {
    const { nguoiDung } = dungXacThuc()
    return (
        <div className="min-h-screen bg-transparent p-0 -mt-20">
             {/* TrangChuyenDoi will take over styling. Reset top margin */}
            <TrangChuyenDoi nguoiDung={nguoiDung} />
        </div>
    )
}

export default TabChuyenDoiAdmin
