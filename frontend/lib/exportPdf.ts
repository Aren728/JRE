export interface PdfExportOptions {
  filename?: string;
  margin?: number | [number, number, number, number];
  scale?: number;
}

export const generateEvaluationPdf = async (
  target: string | HTMLElement = 'report-content-container',
  filenameOrOptions?: string | PdfExportOptions
): Promise<boolean> => {
  if (typeof window === 'undefined' || typeof document === 'undefined' || typeof TextEncoder === 'undefined') {
    return false;
  }

  const filename = typeof filenameOrOptions === 'string'
    ? filenameOrOptions
    : filenameOrOptions?.filename || 'JRE_Kundli_Report.pdf';

  const element = typeof target === 'string'
    ? document.getElementById(target)
    : target;

  if (!element) {
    console.warn(`Export container #${target} not found.`);
    return false;
  }

  const options = {
    margin: [10, 10, 10, 10],
    filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#020617',
    },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const },
    pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
  };

  try {
    const html2pdfModule: any = await import('html2pdf.js');
    const exporter = html2pdfModule.default || (window as any).html2pdf;
    if (exporter) {
      await exporter().set(options).from(element).save();
      return true;
    } else {
      console.warn('html2pdf library could not be loaded in current environment.');
      return false;
    }
  } catch (error) {
    console.error('Failed to generate PDF report:', error);
    return false;
  }
};
