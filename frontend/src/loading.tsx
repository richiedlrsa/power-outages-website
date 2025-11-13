export default function Loading() {
    return (
        <div className="flex flex-col items-center justify-center mt-16 text-center">
            <div className="w-12 h-12 border-4 border-[#2563eb] border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-[374151] text-lg font-medium max-w-md">
                Estamos recopilando los datos de los apagones. <br />
                Por favor, espera un momento...
            </p>
        </div>
    )
}